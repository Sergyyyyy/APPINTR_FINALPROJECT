from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import ParkingSpot, PricingRule, ParkingSession
from .serializers import ParkingSpotSerializer, ParkingSessionSerializer
import math


# 1. Get Available Spots (Populates the Check-In Dropdown)
@api_view(['GET'])
def get_available_spots(request):
    spots = ParkingSpot.objects.filter(is_occupied=False)
    serializer = ParkingSpotSerializer(spots, many=True)
    return Response(serializer.data)


# 2. Check-In Vehicle
@api_view(['POST'])
def check_in(request):
    plate_number = request.data.get('plate_number')
    spot_id = request.data.get('spot_id')

    try:
        spot = ParkingSpot.objects.get(id=spot_id, is_occupied=False)
    except ParkingSpot.DoesNotExist:
        return Response({"error": "Spot is invalid or occupied"}, status=status.HTTP_400_BAD_REQUEST)

    # Create session and set spot to occupied
    session = ParkingSession.objects.create(plate_number=plate_number, spot=spot)
    spot.is_occupied = True
    spot.save()

    return Response(ParkingSessionSerializer(session).data, status=status.HTTP_201_CREATED)


# 3. Get Active Sessions (Populates the right side of the Parking Page)
@api_view(['GET'])
def get_active_sessions(request):
    sessions = ParkingSession.objects.filter(time_out__isnull=True)
    serializer = ParkingSessionSerializer(sessions, many=True)
    return Response(serializer.data)


# 4. Check-Out Vehicle (The Math & Business Logic!)
@api_view(['POST'])
def check_out(request, session_id):
    try:
        session = ParkingSession.objects.get(id=session_id, time_out__isnull=True)
    except ParkingSession.DoesNotExist:
        return Response({"error": "Active session not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get the current pricing rule (defaults to 50 if none exists)
    pricing_rule = PricingRule.objects.first()
    hourly_rate = pricing_rule.hourly_rate if pricing_rule else 50.00

    # Log the exit time
    session.time_out = timezone.now()

    # Calculate duration in hours (rounding up to the nearest hour)
    duration_seconds = (session.time_out - session.time_in).total_seconds()
    hours_parked = math.ceil(duration_seconds / 3600)
    if hours_parked == 0:
        hours_parked = 1  # Minimum charge of 1 hour

    session.total_fee = hours_parked * float(hourly_rate)
    session.save()

    # Free up the physical parking spot
    if session.spot:
        session.spot.is_occupied = False
        session.spot.save()

    return Response(ParkingSessionSerializer(session).data)