from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.GlobalSearchView.as_view(), name='global_search'),
    path('encyclopedia/', views.EncyclopediaListView.as_view(), name='encyclopedia_list'),
    path('encyclopedia/search/', views.EncyclopediaSearchView.as_view(), name='encyclopedia_search'),
    path('encyclopedia/<slug:slug>/', views.EncyclopediaDetailView.as_view(), name='encyclopedia_detail'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('dishes/', views.ReviewDishListView.as_view(), name='review_dish_list'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<slug:slug>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    # API endpoints
    path('api/encyclopedia/search/', views.EncyclopediaSearchApiView.as_view(), name='api_encyclopedia_search'),
    path('api/encyclopedia/suggest/', views.EncyclopediaSuggestApiView.as_view(), name='api_encyclopedia_suggest'),
    path('api/encyclopedia/create/', views.EncyclopediaCreateApiView.as_view(), name='api_encyclopedia_create'),
    path('api/encyclopedia/create-placeholder/', views.EncyclopediaQuickCreateApiView.as_view(), name='api_encyclopedia_quick_create'),
    path('api/encyclopedia/<int:entry_id>/set-parent/', views.EncyclopediaParentApiView.as_view(), name='api_encyclopedia_set_parent'),
    path('api/encyclopedia/<int:entry_id>/convert/', views.EncyclopediaConvertApiView.as_view(), name='api_encyclopedia_convert'),
    path('api/dishes/<int:dish_id>/link/', views.DishLinkApiView.as_view(), name='api_dish_link'),
    path('api/dishes/<int:dish_id>/upload-image/', views.DishImageUploadApiView.as_view(), name='api_dish_image_upload'),
]
