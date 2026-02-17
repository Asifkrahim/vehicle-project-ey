from django.db import models
from django.contrib.auth.models import User

class MaintenanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_brand = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=20)
    maintenance_type = models.CharField(max_length=50)
    odometer_reading = models.PositiveIntegerField()
    next_service_km = models.PositiveIntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.vehicle_brand} {self.vehicle_model} - {self.maintenance_type}"
