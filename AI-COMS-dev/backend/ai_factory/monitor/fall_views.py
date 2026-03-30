from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from monitor.models import Alert

class FallAlertView(APIView):
    def post(self, request):
        data = request.data
        
        alert = Alert.objects.create(
            camera_id=data.get("camera_id"),
            alert_type="fall",
        )
        
        return Response({
            "message": "Fall alert received",
            "alert_id": alert.id
        }, status=status.HTTP_201_CREATED)


class FallStatusView(APIView):
    def get(self, request):
        last_fall = Alert.objects.filter(alert_type="fall").order_by('-timestamp').first()

        if last_fall:
            return Response({
                "camera_id": last_fall.camera_id,
                "time": str(last_fall.timestamp),
                "alert_type": last_fall.alert_type
            })

        return Response({"message": "No fall detected"})
