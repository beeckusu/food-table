"""
Importer for fetching reviews directly from Confluence REST API.
"""

from typing import List, Dict
from datetime import datetime

from .base import BaseImporter
from content.utils.confluence_api import ConfluenceClient, ConfluenceAPIError


class ConfluenceAPIImporter(BaseImporter):
    """Fetches reviews from Confluence REST API"""

    def __init__(self, parent_page_id: str):
        """
        Initialize Confluence API importer.

        Args:
            parent_page_id: Confluence parent page ID to fetch descendants from
        """
        self.parent_page_id = parent_page_id
        self.client = ConfluenceClient()
        self._source_info = None

    def fetch_reviews(self) -> List[Dict]:
        """
        Fetch restaurant review pages from Confluence API.

        This includes:
        - Depth 2 pages: Main restaurant review pages
        - Depth 3 pages: Follow-up visit pages (child pages of main reviews)

        Returns:
            List of page dictionaries with 'storage' format content
        """
        # Get all descendants from parent (these will be depth 2 - main reviews)
        main_reviews = self.client.get_page_descendants(self.parent_page_id)

        # Also fetch children of each main review (depth 3 - follow-up visits)
        all_review_pages = list(main_reviews)  # Start with main reviews

        print(f'Found {len(main_reviews)} main review pages, checking for follow-up visits...')

        followup_count = 0
        for main_review in main_reviews:
            try:
                # Get children of this review page
                children = self.client.get_page_descendants(main_review['id'])
                if children:
                    followup_count += len(children)
                    # Mark these as followups with depth 3
                    for child in children:
                        child['depth'] = 3
                        child['is_followup'] = True
                    all_review_pages.extend(children)
            except ConfluenceAPIError as e:
                print(f'Warning: Failed to fetch children of {main_review["id"]}: {str(e)}')
                continue

        print(f'Found {followup_count} follow-up visit pages')

        # Fetch full content for each review page (deduplicate by page ID)
        reviews_with_content = []
        seen_ids = set()

        for page in all_review_pages:
            page_id = page['id']

            # Skip duplicates
            if page_id in seen_ids:
                continue
            seen_ids.add(page_id)

            try:
                # Get full page content
                full_page = self.client.get_page(page_id)

                # Extract body content in storage format (HTML/XML)
                storage_body = full_page.get('body', {}).get('storage', {}).get('value', '')

                reviews_with_content.append({
                    'id': page_id,
                    'title': page['title'],
                    'body': storage_body,
                    'parent_id': page.get('parentId'),
                    'parent_title': page.get('parentTitle', ''),
                    'format': 'storage',  # Indicates HTML/XML format from Confluence
                    'depth': page.get('depth'),  # Include depth to distinguish main vs follow-up
                    'is_followup': page.get('is_followup', page.get('depth') == 3),  # Flag for follow-up visits
                })
            except ConfluenceAPIError as e:
                # Log error but continue with other pages
                print(f'Warning: Failed to fetch page {page_id} ({page["title"]}): {str(e)}')
                continue

        # Store source info for later
        self._source_info = {
            'source': f'Confluence API - Parent Page {self.parent_page_id}',
            'total_pages': len(reviews_with_content),
            'export_date': datetime.now().strftime('%Y-%m-%d'),
        }

        return reviews_with_content

    def get_source_info(self) -> Dict:
        """Get metadata about the Confluence API source"""
        if self._source_info is None:
            return {
                'source': f'Confluence API - Parent Page {self.parent_page_id}',
                'total_pages': 0,
                'export_date': datetime.now().strftime('%Y-%m-%d'),
            }
        return self._source_info
