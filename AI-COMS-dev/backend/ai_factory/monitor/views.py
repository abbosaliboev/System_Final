# backend/ai_factory/monitor/views.py
"""
Main Views - Alert, Worker, Report CRUD and streaming endpoints.
~180 lines (Summary views moved to summary_views.py)
"""
import cv2
import time
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.core.mail import send_mass_mail
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import StreamingHttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from .models import Alert, Report, Worker
from .serializers import AlertSerializer, ReportSerializer, WorkerSerializer
from .camera_loader import camera_results, frame_queues, start_all

# Re-export summary views for backwards compatibility
from .summary_views import (
    WorkerViolationStatsView, AlertTypeDistributionView,
    AlertTrendAnalysisView, AlertHeatmapView, SafetyScoreView,
    get_date_range, generate_cache_key
)


class AlertPagination(PageNumberPagination):
    """Custom pagination for alerts - configurable page size"""
    page_size = 20  # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 100


# 🔁 Start all camera streams when this view is initialized (runs once)
start_all()

@api_view(['GET'])
def get_live_detections(request):
    # Return camera_results augmented with today's per-camera alert counts (cached)
    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()

    resp = {}
    for cam_key, data in camera_results.items():
        try:
            cam_num = int(str(cam_key).replace("cam", ""))
        except Exception:
            try:
                cam_num = int(cam_key)
            except Exception:
                cam_num = None

        no_helmet_count = 0
        fall_count = 0
        if cam_num is not None:
            cache_key = f"live_counts:{cam_num}:{today.isoformat()}"
            cached = cache.get(cache_key)
            if cached is not None:
                no_helmet_count = cached.get("no_helmet", 0)
                fall_count = cached.get("fall", 0)
            else:
                try:
                    no_helmet_count = Alert.objects.filter(camera_id=cam_num, alert_type="no_helmet", timestamp__date=today).count()
                    fall_count = Alert.objects.filter(camera_id=cam_num, alert_type="fall", timestamp__date=today).count()
                    cache.set(cache_key, {"no_helmet": no_helmet_count, "fall": fall_count}, 5)
                except Exception:
                    no_helmet_count = 0
                    fall_count = 0

        # convert managed dict entry to plain dict if necessary
        try:
            entry = dict(data)
        except Exception:
            entry = data

        entry["today_no_helmet"] = no_helmet_count
        entry["today_fall"] = fall_count
        resp[cam_key] = entry

    return Response(resp)

# 🎥 MJPEG stream endpoint
def mjpeg_stream(request, cam_id):
    def generate():
        while True:
            if cam_id in frame_queues and not frame_queues[cam_id].empty():
                frame = frame_queues[cam_id].get()
                frame = cv2.resize(frame, (640, 360))
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                time.sleep(0.01)
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')


class AlertListView(generics.ListAPIView):
    serializer_class = AlertSerializer
    pagination_class = AlertPagination

    def get_queryset(self):
        camera_id = self.request.query_params.get('camera_id')
        queryset = Alert.objects.all().order_by('-timestamp')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list to support 'per_camera' mode for initial load.
        Query params:
        - per_camera=5 : Returns 5 most recent alerts per camera (no pagination)
        - page=1&page_size=20 : Standard pagination
        """
        per_camera = request.query_params.get('per_camera')
        
        if per_camera:
            try:
                limit = int(per_camera)
            except ValueError:
                limit = 5
            
            # Get unique camera IDs
            camera_ids = Alert.objects.values_list('camera_id', flat=True).distinct()
            
            # Get 'limit' alerts per camera
            result = []
            for cam_id in camera_ids:
                alerts = Alert.objects.filter(camera_id=cam_id).order_by('-timestamp')[:limit]
                result.extend(alerts)
            
            # Sort combined results by timestamp
            result.sort(key=lambda x: x.timestamp, reverse=True)
            
            serializer = self.get_serializer(result, many=True)
            return Response({
                'results': serializer.data,
                'count': len(result),
                'per_camera_mode': True,
                'per_camera_limit': limit
            })
        
        # Standard paginated response
        return super().list(request, *args, **kwargs)
    
class AlertDeleteView(generics.DestroyAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

class WorkerListView(generics.ListAPIView):
    queryset = Worker.objects.filter(is_active=True).order_by('name')
    serializer_class = WorkerSerializer


class ReportListCreateView(generics.ListCreateAPIView):
    queryset = Report.objects.all().order_by('-timestamp')
    serializer_class = ReportSerializer

class ReportRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    lookup_field = 'pk'  

class ReportAlertView(APIView):
    def post(self, request):
        reports = request.data.get("reports", [])
        messages = []
        from_email = settings.DEFAULT_FROM_EMAIL

        for report in reports:
            subject = f"Safety Alert: {report.get('event')} detected"
            message = (
                f"Dear {report.get('name')},\n\n"
                f"An event was detected: {report.get('event')}\n"
                f"Date: {report.get('date')}\n"
                "Please take the necessary action.\n\n"
                "Factory Monitoring System"
            )
            recipient_list = [report.get("email")]
            if report.get("email"):
                messages.append((subject, message, from_email, recipient_list))

        if messages:
            send_mass_mail(tuple(messages), fail_silently=False)
            return Response({"detail": "Emails sent."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "No valid emails found."}, status=status.HTTP_400_BAD_REQUEST)