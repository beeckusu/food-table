"""
Base importer class for fetching review data.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseImporter(ABC):
    """Base class for all importers"""

    @abstractmethod
    def fetch_reviews(self) -> List[Dict]:
        """
        Fetch restaurant review pages from the source.

        Returns:
            List of dictionaries with page data:
            {
                'id': 'page_id',
                'title': 'Restaurant Name',
                'body': 'Page content (format depends on importer)',
                'parent_id': 'parent_page_id',
                'parent_title': 'Category Name',
                'format': 'storage' | 'markdown'  # Indicates content format
            }
        """
        pass

    @abstractmethod
    def get_source_info(self) -> Dict:
        """
        Get metadata about the import source.

        Returns:
            Dictionary with source information:
            {
                'source': 'Description of source',
                'total_pages': int,
                'export_date': 'YYYY-MM-DD',
                ...
            }
        """
        pass
