from django.urls import path
from . import views

urlpatterns = [
    path('', views.food_list, name='food_list'),
    path('add/', views.food_create, name='food_create'),
    path('edit/<int:pk>/', views.food_update, name='food_update'),
    path('delete/<int:pk>/', views.food_delete, name='food_delete'),
    path('profile/', views.profile_form, name='profile_form'),
    path('history/', views.daily_history, name='daily_history_today'),
    path('history/<str:date_str>/', views.daily_history, name='daily_history'),
]
