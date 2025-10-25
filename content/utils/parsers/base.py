"""
Base parser class for extracting review data from content.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, time
from decimal import Decimal


@dataclass
class ParsedDish:
    """Represents a parsed dish from a review"""
    name: str
    rating: int  # 0-100
    cost: Optional[Decimal] = None
    notes: str = ""
    images: List[str] = field(default_factory=list)  # List of image paths


@dataclass
class ParsedReviewData:
    """Represents parsed review data ready for database import"""
    restaurant_name: str
    visit_date: date
    entry_time: time
    party_size: int
    rating: int  # Overall rating 0-100
    dishes: List[ParsedDish] = field(default_factory=list)
    address: str = ""
    location: str = ""
    notes: str = ""
    website: str = ""
    confluence_page_id: Optional[str] = None
    restaurant_images: List[str] = field(default_factory=list)  # List of restaurant image paths


class BaseParser(ABC):
    """Base class for all content parsers"""

    @abstractmethod
    def parse(self, page_id: str, content: str) -> Optional[ParsedReviewData]:
        """
        Parse review content and extract structured data.

        Args:
            page_id: Unique identifier for the page (for metadata)
            content: Raw content to parse

        Returns:
            ParsedReviewData object if parsing succeeds, None if it fails
        """
        pass

    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """
        Check if this parser can handle the given content format.

        Args:
            content: Raw content to check

        Returns:
            True if this parser can handle this format
        """
        pass
