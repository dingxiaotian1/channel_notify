from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create_groups/', views.create_groups, name='create_groups'),
    path('create_users/', views.create_users, name='create_users'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
]