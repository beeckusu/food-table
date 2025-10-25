"""
Parser for Confluence storage format (HTML/XML from REST API).
"""

import re
from typing import Optional
from datetime import datetime, time, date
from decimal import Decimal

from .base import BaseParser, ParsedReviewData, ParsedDish
from content.utils.confluence_api import convert_confluence_storage_to_markdown


class ConfluenceStorageParser(BaseParser):
    """Parses Confluence storage format (HTML/XML) content"""

    def can_parse(self, content: str) -> bool:
        """Check if content is in Confluence storage format"""
        # Storage format contains Confluence-specific XML tags
        return bool(re.search(r'<ac:|<ri:|<table', content))

    def parse(self, page_id: str, content: str) -> Optional[ParsedReviewData]:
        """
        Parse Confluence storage format content.

        Args:
            page_id: Confluence page ID
            content: HTML/XML content from Confluence REST API

        Returns:
            ParsedReviewData if parsing succeeds, None otherwise
        """
        # Convert storage format to markdown-like text
        markdown_content = convert_confluence_storage_to_markdown(content)

        # Now use the same parsing logic as the markdown parser
        # (We'll import and use it to avoid code duplication)
        from .confluence_markdown import ConfluenceMarkdownParser

        markdown_parser = ConfluenceMarkdownParser()
        parsed_data = markdown_parser.parse(page_id, markdown_content)

        if parsed_data:
            parsed_data.confluence_page_id = page_id

        return parsed_data
