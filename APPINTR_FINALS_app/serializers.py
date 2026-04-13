from rest_framework import serializers
from .models import ParkingSpot, PricingRule, ParkingSession

class ParkingSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpot
        fields = '__all__'

class PricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingRule
        fields = '__all__'

class ParkingSessionSerializer(serializers.ModelSerializer):
    # This pulls the actual spot number (like "A-01") instead of just the ID number
    spot_number = serializers.CharField(source='spot.spot_number', read_only=True)

    class Meta:
        model = ParkingSession
        fields = '__all__'