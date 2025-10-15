from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('encyclopedia/', views.EncyclopediaListView.as_view(), name='encyclopedia_list'),
    path('encyclopedia/search/', views.EncyclopediaSearchView.as_view(), name='encyclopedia_search'),
    path('encyclopedia/<slug:slug>/', views.EncyclopediaDetailView.as_view(), name='encyclopedia_detail'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<slug:slug>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
]
