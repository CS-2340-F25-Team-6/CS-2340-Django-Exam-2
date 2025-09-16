from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='accounts.signup'), # type: ignore
    path('login/', views.login, name='accounts.login'), # type: ignore
    path('logout/', views.logout, name='accounts.logout'),
    path('orders/', views.orders, name='accounts.orders'),
]