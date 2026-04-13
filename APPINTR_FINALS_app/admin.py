from django.contrib import admin
from .models import ParkingSpot, PricingRule, ParkingSession

class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ('spot_number', 'is_occupied')
    list_filter = ('is_occupied',)

class ParkingSessionAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'spot', 'time_in', 'time_out', 'total_fee')
    search_fields = ('plate_number',)

admin.site.register(ParkingSpot, ParkingSpotAdmin)
admin.site.register(PricingRule)
admin.site.register(ParkingSession, ParkingSessionAdmin)