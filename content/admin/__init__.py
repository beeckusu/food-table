from .encyclopedia import EncyclopediaAdmin
from .tag import TagAdmin
from .image import ImageAdmin
from .review import ReviewAdmin
from .inlines import ImageInline, EncyclopediaTagInline

__all__ = [
    'EncyclopediaAdmin',
    'TagAdmin',
    'ImageAdmin',
    'ReviewAdmin',
    'ImageInline',
    'EncyclopediaTagInline',
]
