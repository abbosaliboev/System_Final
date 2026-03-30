from django.contrib import admin
from .models import Camera, Detection

# ---- Camera Admin ----
@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active", "added_on")
    list_filter = ("is_active", "location")
    search_fields = ("name", "stream_url", "location")
    ordering = ("-added_on",)

# ---- Detection Admin ----
@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ("detection_type", "camera", "timestamp", "confidence")
    list_filter = ("detection_type", "camera__location", "timestamp")
    search_fields = ("camera__name", "detection_type")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp", "result_json")
    
    # Optional: Display image if image_path is stored
    def has_image(self, obj):
        return bool(obj.image_path)
    has_image.boolean = True
    has_image.short_description = "Image Attached"


# admin.py
from django.contrib import admin
from .models import Worker, Alert

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['workerId', 'name', 'department', 'supervisor', 'is_active', 'hire_date']
    list_filter = ['department', 'supervisor', 'is_active', 'hire_date']
    search_fields = ['workerId', 'name', 'department', 'supervisor']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('workerId', 'name', 'department', 'supervisor')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
