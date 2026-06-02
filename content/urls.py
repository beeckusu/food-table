from django.urls import path
from . import views
from content.views.review_draft_api import ReviewDraftSaveApiView, ReviewDraftRetrieveApiView, ReviewDraftDeleteApiView
from content.views.review_create_api import ReviewCreateApiView

app_name = 'content'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.GlobalSearchView.as_view(), name='global_search'),
    path('encyclopedia/', views.EncyclopediaListView.as_view(), name='encyclopedia_list'),
    path('encyclopedia/search/', views.EncyclopediaSearchView.as_view(), name='encyclopedia_search'),
    path('encyclopedia/<slug:slug>/', views.EncyclopediaDetailView.as_view(), name='encyclopedia_detail'),
    path('restaurants/', views.RestaurantListView.as_view(), name='restaurant_list'),
    path('restaurants/new/', views.RestaurantCreateView.as_view(), name='restaurant_create'),
    path('restaurants/<int:pk>/', views.RestaurantDetailView.as_view(), name='restaurant_detail'),
    path('restaurants/<int:pk>/edit/', views.RestaurantUpdateView.as_view(), name='restaurant_edit'),
    path('restaurants/<int:pk>/toggle-visited/', views.RestaurantToggleVisitedView.as_view(), name='restaurant_toggle_visited'),
    path('restaurants/<int:pk>/dishes/add/', views.RestaurantDishCreateView.as_view(), name='restaurant_dish_create'),
    path('restaurants/<int:pk>/dishes/<int:dish_pk>/edit/', views.RestaurantDishUpdateView.as_view(), name='restaurant_dish_update'),
    path('restaurants/<int:pk>/dishes/<int:dish_pk>/delete/', views.RestaurantDishDeleteView.as_view(), name='restaurant_dish_delete'),
    path('restaurants/<int:pk>/dishes/<int:dish_pk>/mark-tried/', views.RestaurantDishMarkTriedView.as_view(), name='restaurant_dish_mark_tried'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('dishes/', views.ReviewDishListView.as_view(), name='review_dish_list'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<slug:slug>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    # API endpoints
    path('api/restaurants/search/', views.RestaurantSearchApiView.as_view(), name='api_restaurant_search'),
    path('api/encyclopedia/search/', views.EncyclopediaSearchApiView.as_view(), name='api_encyclopedia_search'),
    path('api/encyclopedia/suggest/', views.EncyclopediaSuggestApiView.as_view(), name='api_encyclopedia_suggest'),
    path('api/encyclopedia/create/', views.EncyclopediaCreateApiView.as_view(), name='api_encyclopedia_create'),
    path('api/encyclopedia/create-placeholder/', views.EncyclopediaQuickCreateApiView.as_view(), name='api_encyclopedia_quick_create'),
    path('api/encyclopedia/<int:entry_id>/set-parent/', views.EncyclopediaParentApiView.as_view(), name='api_encyclopedia_set_parent'),
    path('api/encyclopedia/<int:entry_id>/convert/', views.EncyclopediaConvertApiView.as_view(), name='api_encyclopedia_convert'),
    path('api/dishes/<int:dish_id>/link/', views.DishLinkApiView.as_view(), name='api_dish_link'),
    path('api/dishes/<int:dish_id>/upload-image/', views.DishImageUploadApiView.as_view(), name='api_dish_image_upload'),
    path('api/reviews/create/', ReviewCreateApiView.as_view(), name='api_review_create'),
    path('api/reviews/draft/', ReviewDraftSaveApiView.as_view(), name='api_review_draft_save'),
    path('api/reviews/draft/retrieve/', ReviewDraftRetrieveApiView.as_view(), name='api_review_draft_retrieve'),
    path('api/reviews/draft/<str:draft_id>/delete/', ReviewDraftDeleteApiView.as_view(), name='api_review_draft_delete'),
    path('api/review/ai-rewrite/', views.ReviewAIRewriteApiView.as_view(), name='api_review_ai_rewrite'),
    path('api/encyclopedia/ai-prefill/', views.EncyclopediaAIPrefillApiView.as_view(), name='api_encyclopedia_ai_prefill'),
    path('api/encyclopedia/<int:entry_id>/edit/', views.EncyclopediaEditApiView.as_view(), name='api_encyclopedia_edit'),
    path('api/wishlist/bulk/', views.WishlistBulkCreateApiView.as_view(), name='api_wishlist_bulk_create'),
]
