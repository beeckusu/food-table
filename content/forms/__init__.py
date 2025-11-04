"""
Forms package for the content app.
Each form class is in its own module for better organization.
"""

from .review_filter import ReviewFilterForm
from .review_dish_filter import ReviewDishFilterForm

__all__ = [
    'ReviewFilterForm',
    'ReviewDishFilterForm',
]
