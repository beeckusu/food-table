"""
Confluence API client for fetching pages and content.

This module provides a simple interface to the Confluence REST API v2.
Requires CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN to be set in environment.

Usage:
    client = ConfluenceClient()
    descendants = client.get_page_descendants('99811341')
    page_content = client.get_page('103940097')
"""

import requests
import re
from pathlib import Path
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
from django.conf import settings
from html.parser import HTMLParser


class ConfluenceAPIError(Exception):
    """Exception raised for Confluence API errors"""
    pass


def convert_confluence_storage_to_markdown(storage_html: str) -> str:
    """
    Convert Confluence storage format (XML/HTML) to markdown-like text.

    This is a simple converter that handles the basic elements we need for parsing reviews.
    """
    content = storage_html

    # Extract datetime from <time> elements before removing them
    # Example: <time datetime="2025-02-15" /> becomes "2025-02-15"
    def replace_time(match):
        datetime_attr = re.search(r'datetime="([^"]+)"', match.group(0))
        if datetime_attr:
            return datetime_attr.group(1)
        return ''
    content = re.sub(r'<time[^>]*/?>', replace_time, content)

    # Extract image filenames and replace with markers
    # Example: <ac:image>...<ri:attachment ri:filename="image.jpg" />...</ac:image>
    # becomes: ![IMAGE:image.jpg]
    def replace_image(match):
        filename_match = re.search(r'ri:filename="([^"]+)"', match.group(0))
        if filename_match:
            return f'![IMAGE:{filename_match.group(1)}]'
        return ''
    content = re.sub(r'<ac:image[^>]*>.*?</ac:image>', replace_image, content, flags=re.DOTALL)

    # Remove other Confluence-specific XML tags
    content = re.sub(r'<ri:attachment[^>]*/?>', '', content)
    content = re.sub(r'<ac:.*?>', '', content)
    content = re.sub(r'</ac:.*?>', '', content)

    # Convert headings (h1-h6)
    # First remove strong tags inside headings to avoid double bold
    # Add newlines before and after to ensure proper spacing
    for i in range(1, 7):
        content = re.sub(f'<h{i}><strong>(.*?)</strong></h{i}>', lambda m: f'\n\n{"#" * i} **{m.group(1)}**\n\n', content)
        content = re.sub(f'<h{i}>(.*?)</h{i}>', lambda m: f'\n\n{"#" * i} **{m.group(1)}**\n\n', content)

    # Convert tables to markdown-like format
    # This is tricky - we'll do a simple conversion
    content = convert_tables_to_markdown(content)

    # Convert line breaks
    content = content.replace('<br />', '\n')
    content = content.replace('<br/>', '\n')

    # Remove remaining HTML tags but keep content
    content = re.sub(r'<p>(.*?)</p>', r'\1\n\n', content)
    content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content)
    content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)
    content = re.sub(r'<[^>]+>', '', content)

    # Clean up excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

    # Decode HTML entities
    import html
    content = html.unescape(content)  # This handles all HTML entities automatically

    return content.strip()


def convert_tables_to_markdown(html: str) -> str:
    """Convert HTML tables to markdown-like pipe format"""
    # Extract all tables
    table_pattern = r'<table[^>]*>(.*?)</table>'

    def replace_table(match):
        table_html = match.group(1)

        # Extract rows
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL)

        markdown_rows = []
        for row in rows:
            # Extract cells (th or td)
            cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
            cells = re.findall(cell_pattern, row, re.DOTALL)

            # Clean cell content
            cleaned_cells = []
            for cell in cells:
                # Remove inner tags but keep content
                cell_text = re.sub(r'<p>(.*?)</p>', r'\1', cell)
                cell_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', cell_text)
                cell_text = re.sub(r'<[^>]+>', '', cell_text)
                cell_text = cell_text.strip()
                cleaned_cells.append(cell_text)

            # Build markdown row
            if cleaned_cells:
                markdown_row = '| ' + ' | '.join(cleaned_cells) + ' |'
                markdown_rows.append(markdown_row)
                # Add separator after header row if cells contain **
                if any('**' in cell for cell in cleaned_cells):
                    markdown_rows.append('| ' + ' | '.join(['---'] * len(cleaned_cells)) + ' |')

        return '\n' + '\n'.join(markdown_rows) + '\n'

    return re.sub(table_pattern, replace_table, html, flags=re.DOTALL)


class ConfluenceClient:
    """Client for interacting with Confluence REST API v2"""

    def __init__(
        self,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        site_url: Optional[str] = None
    ):
        """
        Initialize Confluence API client.

        Args:
            email: Atlassian account email (defaults to CONFLUENCE_EMAIL setting)
            api_token: Atlassian API token (defaults to CONFLUENCE_API_TOKEN setting)
            site_url: Confluence site URL (defaults to CONFLUENCE_SITE_URL setting)
        """
        self.email = email or getattr(settings, 'CONFLUENCE_EMAIL', None)
        self.api_token = api_token or getattr(settings, 'CONFLUENCE_API_TOKEN', None)
        self.site_url = (site_url or getattr(settings, 'CONFLUENCE_SITE_URL', 'https://gavinlu.atlassian.net')).rstrip('/')

        if not self.email or not self.api_token:
            raise ConfluenceAPIError(
                'Confluence credentials not configured. '
                'Set CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN in your .env file.'
            )

        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.base_url = f'{self.site_url}/wiki/api/v2'

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make a request to the Confluence API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/pages/123')
            **kwargs: Additional arguments to pass to requests

        Returns:
            JSON response as dictionary

        Raises:
            ConfluenceAPIError: If the request fails
        """
        url = f'{self.base_url}{endpoint}'

        try:
            response = requests.request(method, url, auth=self.auth, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ConfluenceAPIError(f'API request failed: {e.response.status_code} - {e.response.text}')
        except requests.exceptions.RequestException as e:
            raise ConfluenceAPIError(f'Network error: {str(e)}')

    def get_page(self, page_id: str) -> Dict:
        """
        Get a single page by ID, including body content.

        Args:
            page_id: Confluence page ID

        Returns:
            Dictionary containing page data with 'body' field
        """
        return self._request('GET', f'/pages/{page_id}', params={'body-format': 'storage'})

    def get_page_descendants(
        self,
        page_id: str,
        limit: int = 100,
        depth: int = None
    ) -> List[Dict]:
        """
        Get all descendant pages of a parent page.

        Args:
            page_id: Parent page ID
            limit: Maximum number of results per page (max 250)
            depth: Maximum depth to traverse (None for all)

        Returns:
            List of page dictionaries with basic info (no body content)
        """
        all_descendants = []
        cursor = None

        params = {'limit': min(limit, 250)}
        if depth is not None:
            params['depth'] = depth

        while True:
            if cursor:
                params['cursor'] = cursor

            data = self._request('GET', f'/pages/{page_id}/descendants', params=params)

            results = data.get('results', [])
            all_descendants.extend(results)

            # Check if there are more pages
            links = data.get('_links', {})
            if 'next' not in links:
                break

            # Extract cursor from next link if pagination continues
            cursor = data.get('_links', {}).get('next', '').split('cursor=')[-1] if 'next' in links else None
            if not cursor:
                break

        return all_descendants

    def get_restaurant_reviews(self, parent_page_id: str) -> List[Dict]:
        """
        Get all restaurant review pages (leaf pages at depth 2) under a parent page.

        This assumes the structure:
        - Parent (e.g., "Toronto") at depth 0
        - Categories (e.g., "Chinese", "Vietnamese") at depth 1
        - Individual restaurants (reviews) at depth 2

        Args:
            parent_page_id: Parent page ID (e.g., "99811341" for Toronto)

        Returns:
            List of dictionaries with full page content:
            {
                'id': '123',
                'title': 'Restaurant Name',
                'body': 'Full page content',
                'parent_id': '456',
                'parent_title': 'Chinese'
            }
        """
        # Get all descendants
        descendants = self.get_page_descendants(parent_page_id)

        # Filter for depth 2 pages (actual restaurant reviews)
        review_pages = [page for page in descendants if page.get('depth') == 2]

        # Fetch full content for each review page
        reviews_with_content = []
        for page in review_pages:
            try:
                # Get full page content
                full_page = self.get_page(page['id'])

                # Extract body content in storage format (HTML/XML)
                storage_body = full_page.get('body', {}).get('storage', {}).get('value', '')

                # Convert Confluence storage format to markdown-like text
                markdown_body = convert_confluence_storage_to_markdown(storage_body)

                reviews_with_content.append({
                    'id': page['id'],
                    'title': page['title'],
                    'body': markdown_body,
                    'parent_id': page.get('parentId'),
                    'parent_title': page.get('parentTitle', ''),
                })
            except ConfluenceAPIError as e:
                # Log error but continue with other pages
                print(f'Warning: Failed to fetch page {page["id"]} ({page["title"]}): {str(e)}')
                continue

        return reviews_with_content

    def get_attachments(self, page_id: str) -> List[Dict]:
        """
        Get all attachments for a page.

        Args:
            page_id: Confluence page ID

        Returns:
            List of attachment dictionaries with metadata
        """
        all_attachments = []
        cursor = None

        while True:
            params = {'limit': 250}
            if cursor:
                params['cursor'] = cursor

            data = self._request('GET', f'/pages/{page_id}/attachments', params=params)

            results = data.get('results', [])
            all_attachments.extend(results)

            # Check for pagination
            links = data.get('_links', {})
            if 'next' not in links:
                break

            cursor = data.get('_links', {}).get('next', '').split('cursor=')[-1] if 'next' in links else None
            if not cursor:
                break

        return all_attachments

    def download_attachment(self, page_id: str, filename: str, output_path: Path) -> bool:
        """
        Download an attachment from a Confluence page.

        Args:
            page_id: Confluence page ID
            filename: Attachment filename
            output_path: Local path to save the file

        Returns:
            True if download succeeded, False otherwise
        """
        try:
            # Get attachments for the page
            attachments = self.get_attachments(page_id)

            # Find the matching attachment
            attachment = None
            for att in attachments:
                if att.get('title') == filename:
                    attachment = att
                    break

            if not attachment:
                print(f'Warning: Attachment {filename} not found on page {page_id}')
                return False

            # Get download URL from attachment
            download_url = attachment.get('_links', {}).get('download')
            if not download_url:
                print(f'Warning: No download URL for {filename}')
                return False

            # Prepend site URL if it's a relative path
            if download_url.startswith('/'):
                download_url = f'{self.site_url}/wiki{download_url}'

            # Download the file
            response = requests.get(download_url, auth=self.auth, stream=True)
            response.raise_for_status()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f'Error downloading {filename}: {str(e)}')
            return False

    def download_page_images(self, page_id: str, output_dir: Path) -> Dict[str, str]:
        """
        Download all image attachments for a page.

        Args:
            page_id: Confluence page ID
            output_dir: Directory to save images (e.g., FoodTable/media/reviews/164069377)

        Returns:
            Dictionary mapping original filename to path relative to MEDIA_ROOT
        """
        downloaded = {}

        try:
            attachments = self.get_attachments(page_id)

            # Filter for image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            image_attachments = [
                att for att in attachments
                if Path(att.get('title', '')).suffix.lower() in image_extensions
            ]

            for attachment in image_attachments:
                filename = attachment.get('title')
                if not filename:
                    continue

                output_path = output_dir / filename
                if self.download_attachment(page_id, filename, output_path):
                    # Return relative path from MEDIA_ROOT
                    media_root = Path(settings.MEDIA_ROOT)
                    relative_path = output_path.relative_to(media_root)
                    downloaded[filename] = str(relative_path).replace('\\', '/')

        except Exception as e:
            print(f'Error downloading images for page {page_id}: {str(e)}')

        return downloaded
