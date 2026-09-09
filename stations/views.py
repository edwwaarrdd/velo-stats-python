from django.http import JsonResponse

from .models import StationRecord


def station_list(request):
    stations = StationRecord.objects.values("station_id", "name", "lat", "lon")
    return JsonResponse({"results": list(stations)})
