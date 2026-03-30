# monitor/models.py
from django.db import models

# ---- CAMERA MODEL ----
class Camera(models.Model):
    VIEWING_ANGLES = [
        ('frontal', 'Frontal (Eye Level)'),
        ('top_down', 'Top-Down (CCTV)'),
        ('angled', 'Angled (45°)'),
    ]
    
    name = models.CharField(max_length=100)
    stream_url = models.URLField()
    location = models.CharField(max_length=100, blank=True)
    viewing_angle = models.CharField(
        max_length=20, 
        choices=VIEWING_ANGLES, 
        default='frontal',
        help_text='Camera mounting angle - affects fall detection thresholds'
    )
    is_active = models.BooleanField(default=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.location})"

# ---- DETECTION EVENT MODEL ----
class Detection(models.Model):
    DETECTION_TYPES = [
        ('PPE', 'PPE'),
        ('FIRE', 'Fire'),

    ]

    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    detection_type = models.CharField(max_length=20, choices=DETECTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(null=True, blank=True)  # Optional
    result_json = models.JSONField()  # Raw YOLO output: class, bbox, etc.
    image_path = models.CharField(max_length=255, blank=True, null=True)  

    def __str__(self):
        return f"{self.detection_type} - {self.camera.name} - {self.timestamp}"


######################### DANGER ZONE ##################
class DangerZone(models.Model):
    camera_id = models.IntegerField()
    zone_name = models.CharField(max_length=100)
    points = models.JSONField()  # Format: [[x1, y1], [x2, y2], ...]

    def __str__(self):
        return f"{self.zone_name} (Camera {self.camera_id})"


######################## ALERTS ############################
from django.db import models
from django.conf import settings

class Alert(models.Model):
    ALERT_TYPES = [
        ('no_helmet', 'No Helmet'),
        ('fire', 'Fire'),
        ('danger_zone', 'Danger Zone'),
        ('fall', 'Fall'),             
    ]

    camera_id = models.IntegerField()
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    worker_id = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    frame_image = models.ImageField(
        upload_to='alert_frames/',
        null=True,
        blank=True,
        verbose_name='Captured Frame'
    )
    frame_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Frame URL'
    )

    def __str__(self):
        return f"[Cam {self.camera_id}] {self.get_alert_type_display()} @ {self.timestamp}"

    def save(self, *args, **kwargs):
        """Avto URL generatsiya"""
        if self.frame_image and not self.frame_url:
            self.frame_url = f"{settings.MEDIA_URL}{self.frame_image}"
        super().save(*args, **kwargs)
    

####################################  WORKER adding via ADMIN PANEL  ###################################
class Worker(models.Model):
    workerId = models.CharField(max_length=20, unique=True, verbose_name="Worker ID")
    name = models.CharField(max_length=100, verbose_name="Full Name")
    department = models.CharField(max_length=100, verbose_name="Department")
    supervisor = models.CharField(max_length=100, verbose_name="Supervisor")
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Worker"
        verbose_name_plural = "Workers"

    def __str__(self):
        return f"{self.workerId} - {self.name}"

##################################### REPORT ######################################

class Report(models.Model):
    worker = models.CharField(max_length=100)
    workerId = models.CharField(max_length=50)
    worker_email = models.EmailField(blank=True, null=True) 
    supervisor = models.CharField(max_length=100)
    event = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    camera_id = models.IntegerField()
    alert_type = models.CharField(max_length=50)
    alert_id = models.IntegerField(null=True, blank=True)
    frame_image = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.worker} - {self.event} - {self.timestamp}"

