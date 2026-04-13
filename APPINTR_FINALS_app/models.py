from django.db import models

class ParkingSpot(models.Model):
    spot_number = models.CharField(max_length=10, unique=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Available"
        return f"{self.spot_number} ({status})"

class PricingRule(models.Model):
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=50.00)

    def __str__(self):
        return f"Current Rate: ₱{self.hourly_rate}/hr"

class ParkingSession(models.Model):
    plate_number = models.CharField(max_length=15)
    spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    total_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.plate_number} at {self.spot.spot_number if self.spot else 'No Spot'}"