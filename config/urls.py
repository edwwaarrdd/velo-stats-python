from django.http import JsonResponse
from django.urls import path


def healthcheck(request):
    return JsonResponse({"message": "ok"}, status=200)


urlpatterns = [
    path("_healthcheck", healthcheck),
]
