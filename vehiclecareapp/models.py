from django.db import models
from django.contrib.auth.models import User

class MaintenanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_brand = models.CharField(max_length=100)
    vehicle_model = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=20, default="UNKNOWN")
    vehicle_type = models.CharField(max_length=50)
    maintenance_type = models.CharField(max_length=100)
    
    # NEW FIELD: COST
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    odometer_reading = models.IntegerField()
    next_service_km = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.vehicle_brand} {self.vehicle_model} ({self.vehicle_number})"