from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('register/',views.login,name="login"),
    path('',views.register,name="register"),
    path('logout/',views.logout,name="logout"),
]