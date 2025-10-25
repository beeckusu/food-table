"""
Importer for loading reviews from JSON export files.
"""

import json
from pathlib import Path
from typing import List, Dict

from .base import BaseImporter


class JSONFileImporter(BaseImporter):
    """Loads reviews from JSON export files"""

    def __init__(self, json_path: Path):
        """
        Initialize JSON file importer.

        Args:
            json_path: Path to JSON export file
        """
        self.json_path = json_path
        self._data = None

    def fetch_reviews(self) -> List[Dict]:
        """
        Load restaurant review pages from JSON file.

        Returns:
            List of page dictionaries with 'markdown' format content
        """
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

        pages = self._data.get('pages', [])

        # Add format indicator to each page
        for page in pages:
            page['format'] = 'markdown'  # JSON exports contain markdown-like content

        return pages

    def get_source_info(self) -> Dict:
        """Get metadata about the JSON file source"""
        if self._data is None:
            # Load data if not already loaded
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

        return self._data.get('export_info', {
            'source': f'JSON file: {self.json_path.name}',
            'total_pages': 0,
        })
