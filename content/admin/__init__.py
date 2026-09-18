from .encyclopedia import EncyclopediaAdmin
from .tag import TagAdmin
from .image import ImageAdmin
from .restaurant import RestaurantAdmin, RestaurantDishAdmin
from .food_festival import FoodFestivalAdmin
from .menu_item import MenuItemAdmin
from .review import ReviewAdmin
from .recipe import RecipeAdmin
from .inlines import ImageInline, EncyclopediaTagInline

__all__ = [
    'EncyclopediaAdmin',
    'TagAdmin',
    'ImageAdmin',
    'RestaurantAdmin',
    'RestaurantDishAdmin',
    'FoodFestivalAdmin',
    'MenuItemAdmin',
    'ReviewAdmin',
    'RecipeAdmin',
    'ImageInline',
    'EncyclopediaTagInline',
]
