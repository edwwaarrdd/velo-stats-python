from django.urls import path

from .views import ride_summary

urlpatterns = [
    path("summary", ride_summary, name="ride-summary"),
]
