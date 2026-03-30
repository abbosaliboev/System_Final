from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import DangerZone
from .serializers import DangerZoneSerializer

# 🔄 List + Create
class DangerZoneListCreateView(generics.ListCreateAPIView):
    serializer_class = DangerZoneSerializer

    def get_queryset(self):
        camera_id = self.request.query_params.get('camera_id')
        if camera_id:
            return DangerZone.objects.filter(camera_id=camera_id)
        return DangerZone.objects.all()

# ❌ Delete by ID (single zone)
@api_view(['DELETE'])
def delete_danger_zone(request, pk):
    try:
        zone = DangerZone.objects.get(pk=pk)
        zone.delete()
        return Response({"status": "deleted"}, status=status.HTTP_204_NO_CONTENT)
    except DangerZone.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

# ❌❌ Delete all zones for a given camera
@api_view(['DELETE'])
def delete_all_danger_zones(request, camera_id):
    deleted_count, _ = DangerZone.objects.filter(camera_id=camera_id).delete()
    return Response({"status": f"{deleted_count} zones deleted"}, status=status.HTTP_204_NO_CONTENT)
