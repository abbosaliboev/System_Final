"""
Summary Views - Dashboard analytics endpoints.
~180 lines - Heatmap, Trend, Safety Score, Violations.
"""
import hashlib
from datetime import datetime
from math import log10

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.core.cache import cache

from .models import Alert, Report


def get_date_range(request):
    """Parse start and end dates from request query params"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    try:
        if start and end:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        else:
            end_date = datetime.today()
            start_date = end_date.replace(day=1)
    except Exception:
        return None, None
    return start_date, end_date


def generate_cache_key(prefix, start_date, end_date):
    """Generate unique cache key based on date range"""
    date_str = f"{start_date.date()}_{end_date.date()}"
    return f"{prefix}_{hashlib.md5(date_str.encode()).hexdigest()}"


class WorkerViolationStatsView(APIView):
    """Violation counts grouped by worker ID"""
    def get(self, request):
        start_date, end_date = get_date_range(request)
        cache_key = generate_cache_key('worker_violations', start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = Report.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(
                timestamp__date__gte=start_date.date(),
                timestamp__date__lte=end_date.date()
            )
        
        data = list(queryset.values('workerId').annotate(violation_count=Count('id')).order_by('-violation_count'))
        cache.set(cache_key, data, 300)
        return Response(data)


class AlertTypeDistributionView(APIView):
    """Alert counts by type (pie chart data)"""
    def get(self, request):
        start_date, end_date = get_date_range(request)
        cache_key = generate_cache_key('alert_distribution', start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = Alert.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(
                timestamp__date__gte=start_date.date(),
                timestamp__date__lte=end_date.date()
            )
        
        data = list(queryset.values('alert_type').annotate(count=Count('id')).order_by('-count'))
        result = [{'alert_type': item['alert_type'], 'count': item['count']} for item in data]
        cache.set(cache_key, result, 300)
        return Response(result)


class AlertTrendAnalysisView(APIView):
    """Alert trends by weekday (line chart data)"""
    def get(self, request):
        start_date, end_date = get_date_range(request)
        cache_key = generate_cache_key('alert_trend', start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = Alert.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(
                timestamp__date__gte=start_date.date(),
                timestamp__date__lte=end_date.date()
            )
        
        data = queryset.annotate(weekday=ExtractWeekDay('timestamp')).values('weekday', 'alert_type').annotate(count=Count('id'))
        
        weekday_map = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
        trend = {
            "labels": [weekday_map[i] for i in range(1, 8)],
            "danger_zone": [0] * 7, "no_helmet": [0] * 7, "fire": [0] * 7, "fall": [0] * 7,
        }
        
        for entry in data:
            idx = entry['weekday'] - 1
            if entry['alert_type'] in trend:
                trend[entry['alert_type']][idx] = entry['count']
        
        cache.set(cache_key, trend, 300)
        return Response(trend)


class AlertHeatmapView(APIView):
    """Alert heatmap (weekday x hour matrix)"""
    def get(self, request):
        start_date, end_date = get_date_range(request)
        if not start_date or not end_date:
            return Response({"error": "Invalid date format"}, status=400)
        
        cache_key = generate_cache_key('alert_heatmap', start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        alerts = (
            Alert.objects.filter(timestamp__date__gte=start_date.date(), timestamp__date__lte=end_date.date())
            .annotate(weekday=ExtractWeekDay('timestamp'), hour=ExtractHour('timestamp'))
            .values('weekday', 'hour').annotate(count=Count('id'))
        )

        matrix = [[0 for _ in range(24)] for _ in range(7)]
        for entry in alerts:
            weekday = (entry['weekday'] + 5) % 7
            matrix[weekday][entry['hour']] = entry['count']

        result = {
            "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "hours": list(range(24)),
            "matrix": matrix
        }
        cache.set(cache_key, result, 300)
        return Response(result)


class SafetyScoreView(APIView):
    """Calculate weighted safety score"""
    def get(self, request):
        start_date, end_date = get_date_range(request)
        cache_key = generate_cache_key('safety_score', start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = Alert.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(timestamp__date__gte=start_date.date(), timestamp__date__lte=end_date.date())
        
        weights = {"no_helmet": 1, "danger_zone": 2, "fire": 5, "fall": 3}
        alert_counts = queryset.values('alert_type').annotate(count=Count('id'))
        
        counts = {k: 0 for k in weights}
        for item in alert_counts:
            if item['alert_type'] in counts:
                counts[item['alert_type']] = item['count']
        
        penalty = sum(counts[t] * weights[t] for t in weights)
        score = max(round(100 - 15 * log10(1 + penalty)), 50)
        
        total_alerts = sum(counts.values())
        percentages = {t: round(counts[t] / total_alerts * 100) if total_alerts > 0 else 0 for t in counts}
        
        breakdown = [
            {"label": "Danger Zone", "count": counts["danger_zone"], "percent": percentages["danger_zone"]},
            {"label": "No Helmet", "count": counts["no_helmet"], "percent": percentages["no_helmet"]},
            {"label": "Fire", "count": counts["fire"], "percent": percentages["fire"]},
            {"label": "Fall", "count": counts["fall"], "percent": percentages["fall"]},
        ]
        
        result = {"safety_score": score, "total_weighted_penalty": penalty, "breakdown": breakdown}
        cache.set(cache_key, result, 300)
        return Response(result)
