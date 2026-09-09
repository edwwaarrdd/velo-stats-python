from django.urls import path

from .views import ride_list, ride_summary

urlpatterns = [
    path("", ride_list, name="ride-list"),
    path("summary", ride_summary, name="ride-summary"),
]
