from .home import HomeView
from .encyclopedia_list import EncyclopediaListView
from .encyclopedia_detail import EncyclopediaDetailView
from .encyclopedia_search import EncyclopediaSearchView
from .encyclopedia_search_api import EncyclopediaSearchApiView
from .dish_link_api import DishLinkApiView
from .review_list import ReviewListView
from .review_detail import ReviewDetailView
from .recipe_list import RecipeListView
from .recipe_detail import RecipeDetailView
from .global_search import GlobalSearchView

__all__ = [
    'HomeView',
    'EncyclopediaListView',
    'EncyclopediaDetailView',
    'EncyclopediaSearchView',
    'EncyclopediaSearchApiView',
    'DishLinkApiView',
    'ReviewListView',
    'ReviewDetailView',
    'RecipeListView',
    'RecipeDetailView',
    'GlobalSearchView',
]
