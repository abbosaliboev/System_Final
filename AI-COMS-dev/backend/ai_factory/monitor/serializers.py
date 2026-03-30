# serializers.py
from rest_framework import serializers
from .models import Detection, DangerZone, Alert, Report, Worker

class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = '__all__'

class DangerZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DangerZone
        fields = '__all__'


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['timestamp']

class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['workerId', 'name', 'department', 'supervisor', 'phone', 'email', 'is_active']
        
    def to_representation(self, instance):
        # Only return active workers
        if not instance.is_active:
            return None
        return super().to_representation(instance)

# serializers.py
class ReportSerializer(serializers.ModelSerializer):
    worker_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = '__all__'
    
    def get_worker_email(self, obj):
        # Get email from Worker model using workerId
        try:
            from .models import Worker
            worker = Worker.objects.get(workerId=obj.workerId)
            return worker.email
        except Worker.DoesNotExist:
            return None
