from .encyclopedia import EncyclopediaAdmin
from .tag import TagAdmin
from .image import ImageAdmin
from .restaurant import RestaurantAdmin
from .review import ReviewAdmin
from .recipe import RecipeAdmin
from .inlines import ImageInline, EncyclopediaTagInline

__all__ = [
    'EncyclopediaAdmin',
    'TagAdmin',
    'ImageAdmin',
    'RestaurantAdmin',
    'ReviewAdmin',
    'RecipeAdmin',
    'ImageInline',
    'EncyclopediaTagInline',
]
