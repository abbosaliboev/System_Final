# backend/ai_factory/monitor/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .report_pdf_views import GeneratePDFReportView
from .views import (
    AlertDeleteView,
    AlertHeatmapView,
    AlertTrendAnalysisView,
    AlertTypeDistributionView,
    ReportAlertView,
    ReportListCreateView,
    ReportRetrieveUpdateView,
    SafetyScoreView,
    WorkerListView,
    WorkerViolationStatsView,
    get_live_detections,
    AlertListView,
)
from .stream_views import video_feed
from . import dangerzone_views
from . import fall_views  # ✅ Yangi qo‘shildi (fall uchun)

urlpatterns = [
    # 🔴 LIVE DETECTION
    path('live/', get_live_detections),                 # /api/live/
    path('live/<str:cam_id>/', video_feed),            # /api/video/cam1/
    
    # ⚠️ DANGER ZONES
    path('danger-zones/', dangerzone_views.DangerZoneListCreateView.as_view(), name='danger-zone-list-create'),
    path('danger-zones/<int:pk>/', dangerzone_views.delete_danger_zone, name='danger-zone-delete'),
    path('danger-zones/delete_all/<int:camera_id>/', dangerzone_views.delete_all_danger_zones, name='danger-zone-delete-all'),

    # 🔔 ALERTS
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/', AlertDeleteView.as_view(), name='alert-delete'),

    # 👷‍♂️ WORKERS
    path('workers/', WorkerListView.as_view(), name='worker-list'),

    # 🧾 REPORTS
    path('reports/', ReportListCreateView.as_view(), name='report-list-create'),
    path('reports/<int:pk>/', ReportRetrieveUpdateView.as_view(), name='report-edit'),

    # 📢 ALERT REPORT LINK
    path('reports/alert/', ReportAlertView.as_view(), name='report-alert'),

    # 🧩 PDF DOWNLOAD
    path('reports/download-pdf/', GeneratePDFReportView.as_view(), name='download-pdf'),

    # 👷‍♂️ WORKER VIOLATION STATS
    path('reports/worker-violations/', WorkerViolationStatsView.as_view(), name='worker-violation-stats'),

    # 📊 ALERT DISTRIBUTION
    path('alerts/distribution/', AlertTypeDistributionView.as_view(), name='alert-distribution'),

    # 📈 TREND LINE CHART
    path('alerts/trend/', AlertTrendAnalysisView.as_view(), name='alert-trend'),

    # 🌡️ HEATMAP
    path('alerts/heatmap/', AlertHeatmapView.as_view(), name='alert-heatmap'),

    # 🛡️ SAFETY SCORE
    path('alerts/safety-score/', SafetyScoreView.as_view(), name='safety-score'),

    # 🧍 FALL DETECTION (✅ Yangi qo‘shildi)
    path('fall/alert/', fall_views.FallAlertView.as_view(), name='fall-alert'),
    path('fall/status/', fall_views.FallStatusView.as_view(), name='fall-status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
