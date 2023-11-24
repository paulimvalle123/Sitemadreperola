from django.contrib import admin
from django.urls import include, path
from importer import views
urlpatterns = [
    path('', include('importer.urls')),
    
]
