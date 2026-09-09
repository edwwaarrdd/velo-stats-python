from django.http import JsonResponse
from django.urls import include, path


def healthcheck(request):
    return JsonResponse({"message": "ok"}, status=200)


urlpatterns = [
    path("_healthcheck", healthcheck),
    path("rides/", include("rides.urls")),
]
