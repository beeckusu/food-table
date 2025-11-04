from .home import HomeView
from .encyclopedia_list import EncyclopediaListView
from .encyclopedia_detail import EncyclopediaDetailView
from .encyclopedia_search import EncyclopediaSearchView
from .encyclopedia_search_api import EncyclopediaSearchApiView
from .encyclopedia_suggest_api import EncyclopediaSuggestApiView
from .encyclopedia_create_api import EncyclopediaCreateApiView
from .dish_link_api import DishLinkApiView
from .dish_image_api import DishImageUploadApiView
from .review_list import ReviewListView
from .review_detail import ReviewDetailView
from .review_dish_list import ReviewDishListView
from .recipe_list import RecipeListView
from .recipe_detail import RecipeDetailView
from .global_search import GlobalSearchView

__all__ = [
    'HomeView',
    'EncyclopediaListView',
    'EncyclopediaDetailView',
    'EncyclopediaSearchView',
    'EncyclopediaSearchApiView',
    'EncyclopediaSuggestApiView',
    'EncyclopediaCreateApiView',
    'DishLinkApiView',
    'DishImageUploadApiView',
    'ReviewListView',
    'ReviewDetailView',
    'ReviewDishListView',
    'RecipeListView',
    'RecipeDetailView',
    'GlobalSearchView',
]
