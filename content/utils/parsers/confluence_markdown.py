"""
Parser for Confluence markdown format (from JSON exports or MCP tools).
"""

import re
from typing import Optional, List, Dict
from datetime import datetime, time
from decimal import Decimal

from .base import BaseParser, ParsedReviewData, ParsedDish


class ConfluenceMarkdownParser(BaseParser):
    """Parses Confluence markdown format content"""

    def can_parse(self, content: str) -> bool:
        """Check if content is in markdown format"""
        # Markdown format contains tables with | characters and headings with #
        return bool(re.search(r'\|.*\|', content) or re.search(r'#\s+', content))

    def parse(self, page_id: str, content: str) -> Optional[ParsedReviewData]:
        """
        Parse Confluence markdown format content.

        Args:
            page_id: Confluence page ID
            content: Markdown content

        Returns:
            ParsedReviewData if parsing succeeds, None otherwise
        """
        # Parse restaurant info and visit details
        visit_info = self.parse_visit_info(content)

        if not visit_info:
            return None

        # Extract restaurant images (images before first dish heading)
        restaurant_images = self.extract_restaurant_images(content, page_id)

        # Parse all dish reviews (including their images)
        dishes = self.parse_dishes(content, page_id)

        # Calculate overall rating (average of all dish ratings)
        overall_rating = self.calculate_overall_rating(dishes)

        # Build parsed data
        return ParsedReviewData(
            restaurant_name=visit_info.get('restaurant_name', 'Unknown'),
            visit_date=visit_info['date'],
            entry_time=visit_info['time'],
            party_size=visit_info['party_size'],
            rating=overall_rating,
            dishes=dishes,
            address=visit_info.get('address', ''),
            location=visit_info.get('location', ''),
            notes=visit_info.get('notes', ''),
            website=visit_info.get('website', ''),
            confluence_page_id=page_id,
            restaurant_images=restaurant_images,
        )

    def parse_visit_info(self, body_content: str) -> Optional[Dict]:
        """Extract visit information from the top table"""
        info = {}

        # Extract address
        address_match = re.search(r'\|\s*Address\s*\|\s*([^\|]+)\s*\|', body_content, re.IGNORECASE)
        if address_match:
            info['address'] = address_match.group(1).strip()
            # Use address as location too
            info['location'] = address_match.group(1).strip()

        # Extract date (handle both plain text and Confluence date widget)
        date_match = re.search(r'\|\s*Date\s*\|\s*(?:<custom[^>]*>)?([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4}|[A-Za-z]+\s+[0-9]{1,2}\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})', body_content, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1).strip()
            info['date'] = self.parse_date(date_str)
        else:
            return None  # Date is required

        # Extract time
        time_match = re.search(r'\|\s*Time of Entry\s*\|\s*([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)', body_content, re.IGNORECASE)
        if time_match:
            time_str = time_match.group(1).strip()
            info['time'] = self.parse_time(time_str)
        else:
            info['time'] = time(12, 0)  # Default to noon if not found

        # Extract party size
        party_match = re.search(r'\|\s*Party\s*\|\s*([^\|]+)\s*\|', body_content, re.IGNORECASE)
        if party_match:
            party_str = party_match.group(1).strip()
            info['party_size'] = self.parse_party_size(party_str)
        else:
            info['party_size'] = 1  # Default to 1

        # Extract website (optional)
        website_match = re.search(r'\|\s*Website\s*\|.*?https?://([^\s<\|]+)', body_content, re.IGNORECASE)
        if website_match:
            info['website'] = 'https://' + website_match.group(1)

        # Extract any notes before the first dish section
        # Look for text after the Order table but before the first dish heading
        # First, find everything after the Total row
        total_match = re.search(r'\|\s*\*\*Total\*\*.*?\|\s*\n', body_content, re.DOTALL)
        if total_match:
            # Get content after the Total row
            content_after_total = body_content[total_match.end():]

            # Find the first dish heading (starts with # **)
            first_dish_match = re.search(r'\n#\s*\*\*', content_after_total)

            if first_dish_match:
                # Extract text between Total and first dish heading
                potential_notes = content_after_total[:first_dish_match.start()].strip()

                # Clean up formatting
                potential_notes = re.sub(r'\u200c', '', potential_notes)  # Remove zero-width spaces
                potential_notes = re.sub(r'<[^>]+>', '', potential_notes)  # Remove HTML tags
                potential_notes = re.sub(r'!\[.*?\]\(.*?\)', '', potential_notes)  # Remove images
                # Remove markdown table separators and fragments
                potential_notes = re.sub(r'(?:[A-Z][a-z]{0,3}\s*)?\n(?:\|[^\n]*\|\s*\n)+', '', potential_notes)
                potential_notes = re.sub(r'.*?---.*?\|.*?', '', potential_notes)
                potential_notes = re.sub(r'\|\s*---.*', '', potential_notes)
                potential_notes = re.sub(r'\n\s*\n\s*\n+', '\n\n', potential_notes)  # Clean excessive newlines
                potential_notes = potential_notes.strip()

                # Only include if substantial and doesn't look like a heading
                if potential_notes and len(potential_notes) > 20 and not potential_notes.startswith('#'):
                    info['notes'] = potential_notes[:1000]  # Limit length

        return info if info.get('date') else None

    def parse_date(self, date_str: str) -> datetime.date:
        """Parse various date formats"""
        # Try different formats
        formats = [
            '%m/%d/%Y',  # 11/6/2024
            '%m-%d-%Y',  # 11-6-2024
            '%Y-%m-%d',  # 2024-11-06
            '%B %d %Y',  # November 6 2024
            '%b %d %Y',  # Nov 6 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # If all else fails, try to extract numbers
        nums = re.findall(r'\d+', date_str)
        if len(nums) >= 3:
            # Assume month/day/year or year-month-day
            if int(nums[0]) > 12:  # Year first
                return datetime(int(nums[0]), int(nums[1]), int(nums[2])).date()
            else:  # Month first
                year = int(nums[2]) if int(nums[2]) > 2000 else int(nums[2]) + 2000
                return datetime(year, int(nums[0]), int(nums[1])).date()

        raise ValueError(f'Could not parse date: {date_str}')

    def parse_time(self, time_str: str) -> time:
        """Parse time string"""
        time_str = time_str.strip().upper()

        # Handle 12-hour format with AM/PM
        match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            am_pm = match.group(3)

            if am_pm:
                if am_pm == 'PM' and hour != 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0

            return time(hour, minute)

        return time(12, 0)  # Default

    def parse_party_size(self, party_str: str) -> int:
        """Extract party size from string"""
        # Handle "Self"
        if 'self' in party_str.lower():
            return 1

        # Handle text numbers
        text_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        for word, num in text_numbers.items():
            if word in party_str.lower():
                return num

        # Extract first number found
        match = re.search(r'\d+', party_str)
        if match:
            return int(match.group())

        return 1  # Default

    def extract_restaurant_images(self, body_content: str, page_id: str) -> List[str]:
        """
        Extract images that appear before the first dish heading.
        These are assumed to be restaurant images.

        Args:
            body_content: Full markdown content
            page_id: Confluence page ID for constructing paths

        Returns:
            List of image paths relative to FoodTable/images/
        """
        # Find first dish heading position
        first_dish_match = re.search(r'\n#\s*\*\*', body_content)

        if first_dish_match:
            # Get content before first dish
            before_dishes = body_content[:first_dish_match.start()]
        else:
            # No dishes found, check entire content
            before_dishes = body_content

        # Extract image markers
        image_markers = re.findall(r'!\[IMAGE:([^\]]+)\]', before_dishes)

        # Convert to paths: reviews/{page_id}/{filename}
        return [f'reviews/{page_id}/{filename}' for filename in image_markers]

    def parse_dishes(self, body_content: str, page_id: str) -> List[ParsedDish]:
        """Extract all dish reviews from the page"""
        dishes = []

        # Find all dish sections (starts with # **Dish Name**)
        dish_pattern = r'#\s*\*\*([^*]+)\*\*\s*(.*?)(?=\n#\s*\*\*|\Z)'
        dish_matches = re.finditer(dish_pattern, body_content, re.DOTALL)

        for match in dish_matches:
            dish_name = match.group(1).strip()
            dish_content = match.group(2).strip()

            # Extract overall rating
            rating_match = re.search(r'\*\*Overall Rating\s*-\s*(\d+)(?:/100)?\*\*', dish_content, re.IGNORECASE)
            if not rating_match:
                # Try table format
                rating_match = re.search(r'\|\s*\*\*Rating\*\*\s*\|\s*(\d+)\s*\|', dish_content)

            if not rating_match:
                continue  # Skip dishes without ratings

            rating = int(rating_match.group(1))

            # Extract cost
            cost = None
            cost_match = re.search(r'\|\s*\*\*Cost\*\*\s*\|\s*\$?\s*([0-9.]+)\s*\|', dish_content)
            if cost_match:
                cost = Decimal(cost_match.group(1))

            # Extract images from dish content
            dish_images = re.findall(r'!\[IMAGE:([^\]]+)\]', dish_content)
            dish_image_paths = [f'reviews/{page_id}/{filename}' for filename in dish_images]

            # Extract detailed notes
            notes_parts = []

            # First, try to find free-form text BEFORE "Overall Rating"
            # This captures review text that appears between dish name and the rating
            freeform_match = re.search(r'^(.*?)(?=\*\*Overall Rating)', dish_content, re.DOTALL)

            if freeform_match:
                freeform_text = freeform_match.group(1).strip()
                # Clean up the text
                # Remove image markers (![IMAGE:filename])
                freeform_text = re.sub(r'!\[IMAGE:[^\]]+\]', '', freeform_text)
                # Remove other image references
                freeform_text = re.sub(r'!\[.*?\]\(.*?\)', '', freeform_text)
                # Remove rating detail tables (contain Ra + table rows with Rating/Dish/Cost/Date)
                # These unwanted tables appear after text content but before Overall Rating
                freeform_text = re.sub(r'(?:[A-Z][a-z]{0,3}\s*)?\n(?:\|[^\n]*\|\s*\n)+', '', freeform_text)
                # Remove zero-width space markers
                freeform_text = re.sub(r'\u200c', '', freeform_text)
                # Remove excessive newlines
                freeform_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', freeform_text)
                freeform_text = freeform_text.strip()

                # Check if this is actually structured content (has Texture/Taste/Presentation)
                has_structured = bool(re.search(r'\*\*Texture\s*-', freeform_text) or
                                     re.search(r'\*\*Taste\s*-', freeform_text) or
                                     re.search(r'\*\*Presentation\s*-', freeform_text))

                if not has_structured and freeform_text and len(freeform_text) > 20:
                    # This is pure free-form review text
                    notes_parts.append(freeform_text)

            # If no free-form text, parse structured sections (Texture/Taste/Presentation)
            if not notes_parts:
                # Texture
                texture_match = re.search(r'\*\*Texture\s*-\s*([0-9.]+/5)\*\*\s*\n\s*(.*?)(?=\n\*\*|\Z)', dish_content, re.DOTALL)
                if texture_match:
                    notes_parts.append(f"Texture ({texture_match.group(1)}): {texture_match.group(2).strip()}")

                # Taste
                taste_match = re.search(r'\*\*Taste\s*-\s*([0-9.]+/5)\*\*\s*\n\s*(.*?)(?=\n\*\*|\Z)', dish_content, re.DOTALL)
                if taste_match:
                    notes_parts.append(f"Taste ({taste_match.group(1)}): {taste_match.group(2).strip()}")

                # Presentation
                presentation_match = re.search(r'\*\*Presentation\s*-\s*([0-9.]+/5)\*\*\s*\n\s*(.*?)(?=\n\*\*|\Z)', dish_content, re.DOTALL)
                if presentation_match:
                    notes_parts.append(f"Presentation ({presentation_match.group(1)}): {presentation_match.group(2).strip()}")

            notes = '\n\n'.join(notes_parts) if notes_parts else ''

            # Final cleanup: Remove any rating detail tables that made it through
            if notes:
                notes = re.sub(r'(?:[A-Z][a-z]{0,3}\s*)?\n(?:\|[^\n]*\|\s*\n)+', '', notes)
                # Remove any remaining markdown table separator rows and fragments
                notes = re.sub(r'.*?---.*?\|.*?', '', notes)
                notes = re.sub(r'\|\s*---.*', '', notes)
                notes = re.sub(r'\n\s*\n\s*\n+', '\n\n', notes).strip()

            dishes.append(ParsedDish(
                name=dish_name,
                rating=rating,
                cost=cost,
                notes=notes[:2000] if notes else '',  # Limit length
                images=dish_image_paths
            ))

        return dishes

    def calculate_overall_rating(self, dishes: List[ParsedDish]) -> int:
        """Calculate overall review rating from dish ratings"""
        if not dishes:
            return 50  # Default neutral rating

        # Use average of all dish ratings
        total = sum(dish.rating for dish in dishes)
        return round(total / len(dishes))
