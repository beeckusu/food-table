from .home import HomeView
from .restaurant_list import RestaurantListView
from .restaurant_detail import (
    RestaurantDetailView,
    RestaurantToggleVisitedView,
    RestaurantDishCreateView,
    RestaurantDishUpdateView,
    RestaurantDishDeleteView,
    RestaurantDishMarkTriedView,
)
from .restaurant_create import RestaurantCreateView
from .encyclopedia_list import EncyclopediaListView
from .encyclopedia_detail import EncyclopediaDetailView
from .encyclopedia_search import EncyclopediaSearchView
from .restaurant_search_api import RestaurantSearchApiView
from .encyclopedia_search_api import EncyclopediaSearchApiView
from .encyclopedia_suggest_api import EncyclopediaSuggestApiView
from .encyclopedia_create_api import EncyclopediaCreateApiView
from .encyclopedia_parent_api import EncyclopediaParentApiView
from .encyclopedia_convert_api import EncyclopediaConvertApiView
from .encyclopedia_quick_create_api import EncyclopediaQuickCreateApiView
from .dish_link_api import DishLinkApiView
from .dish_image_api import DishImageUploadApiView
from .review_list import ReviewListView
from .review_detail import ReviewDetailView
from .review_dish_list import ReviewDishListView
from .review_create_api import ReviewCreateApiView
from .review_draft_api import ReviewDraftSaveApiView, ReviewDraftRetrieveApiView, ReviewDraftDeleteApiView
from .recipe_list import RecipeListView
from .recipe_detail import RecipeDetailView
from .global_search import GlobalSearchView
from .review_ai_rewrite_api import ReviewAIRewriteApiView
from .encyclopedia_ai_prefill_api import EncyclopediaAIPrefillApiView
from .encyclopedia_edit_api import EncyclopediaEditApiView

__all__ = [
    'HomeView',
    'RestaurantListView',
    'RestaurantDetailView',
    'RestaurantToggleVisitedView',
    'RestaurantDishCreateView',
    'RestaurantDishUpdateView',
    'RestaurantDishDeleteView',
    'RestaurantDishMarkTriedView',
    'RestaurantCreateView',
    'EncyclopediaListView',
    'EncyclopediaDetailView',
    'EncyclopediaSearchView',
    'RestaurantSearchApiView',
    'EncyclopediaSearchApiView',
    'EncyclopediaSuggestApiView',
    'EncyclopediaCreateApiView',
    'EncyclopediaParentApiView',
    'EncyclopediaConvertApiView',
    'EncyclopediaQuickCreateApiView',
    'DishLinkApiView',
    'DishImageUploadApiView',
    'ReviewListView',
    'ReviewDetailView',
    'ReviewDishListView',
    'ReviewCreateApiView',
    'ReviewDraftSaveApiView',
    'ReviewDraftRetrieveApiView',
    'ReviewDraftDeleteApiView',
    'RecipeListView',
    'RecipeDetailView',
    'GlobalSearchView',
    'ReviewAIRewriteApiView',
    'EncyclopediaAIPrefillApiView',
    'EncyclopediaEditApiView',
]
