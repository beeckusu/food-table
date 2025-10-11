from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('encyclopedia/', views.EncyclopediaListView.as_view(), name='encyclopedia_list'),
    path('encyclopedia/search/', views.EncyclopediaSearchView.as_view(), name='encyclopedia_search'),
    path('encyclopedia/<slug:slug>/', views.EncyclopediaDetailView.as_view(), name='encyclopedia_detail'),
]
