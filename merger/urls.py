from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyse/', views.analyse, name='analyse'),
    path('merge/', views.merge, name='merge'),
    path('download/<str:filename>/', views.download, name='download'),
    path('reset/', views.reset, name='reset'),
]
