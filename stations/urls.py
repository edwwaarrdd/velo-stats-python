from django.urls import path

from .views import station_list

urlpatterns = [
    path("", station_list, name="station-list"),
]
