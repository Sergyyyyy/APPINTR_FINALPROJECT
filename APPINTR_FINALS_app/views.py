from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import ParkingSpot, PricingRule, ParkingSession
from .serializers import ParkingSpotSerializer, ParkingSessionSerializer
import math
from django.db.models import Sum
from django.utils import timezone
from .models import SystemSetting


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
    settings = SystemSetting.objects.first()
    hourly_rate = settings.hourly_rate if settings else 50.00

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


# 5. Get Dashboad Metrics (Available Spots & Revenue)
@api_view(['GET'])
def get_dashboard_metrics(request):
    # Total capacity is hardcoded as per wireframe note
    total_capacity = 20

    # Calculate available spots
    available_spots = ParkingSpot.objects.filter(is_occupied=False).count()

    # Calculate total revenue from all completed sessions
    revenue_data = ParkingSession.objects.filter(time_out__isnull=False).aggregate(total_rev=Sum('total_fee'))
    total_revenue = revenue_data['total_rev'] if revenue_data['total_rev'] else 0.00

    return Response({
        "total_capacity": total_capacity,
        "available_spots": available_spots,
        "total_revenue": total_revenue
    })


# 6. Get Recent Activity (Merges Check-Ins and Check-Outs)
@api_view(['GET'])
def get_recent_activity(request):
    # Get the last 10 entries of ANY activity, ordered by time
    recent_sessions = ParkingSession.objects.all().order_by('-time_in')[:10]

    # We will manually construct the JSON to match the "Action" column in the wireframe
    activity_data = []

    for session in recent_sessions:
        # Check-In Activity (Always exists)
        check_in_activity = {
            "action": "Check-In",
            "plate": session.plate_number,
            "spot": session.spot.spot_number if session.spot else "N/A",
            "time": session.time_in,  # Backend will send full ISO time, JS will format
        }
        activity_data.append(check_in_activity)

        # Check-Out Activity (Only exists if time_out is set)
        if session.time_out:
            check_out_activity = {
                "action": "Check-Out",
                "plate": session.plate_number,
                "spot": session.spot.spot_number if session.spot else "N/A",
                "time": session.time_out,
            }
            activity_data.append(check_out_activity)

    # Sort the combined list again by time to make sure Check-Outs appear first if newer
    activity_data.sort(key=lambda x: x['time'], reverse=True)

    # Return only the top 10 activities to keep the UI clean
    return Response(activity_data[:10])


# 7. List all spots or Create a new spot
@api_view(['GET', 'POST'])
def manage_spots_api(request):
    if request.method == 'GET':
        # Get all spots, ordered alphabetically/numerically
        spots = ParkingSpot.objects.all().order_by('spot_number')
        serializer = ParkingSpotSerializer(spots, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Create a new spot
        serializer = ParkingSpotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# 8. Update or Delete a specific spot
@api_view(['PUT', 'DELETE'])
def manage_spot_detail_api(request, pk):
    try:
        spot = ParkingSpot.objects.get(pk=pk)
    except ParkingSpot.DoesNotExist:
        return Response({'error': 'Spot not found'}, status=404)

    if request.method == 'PUT':
        # Update the spot number (partial=True means we only update the fields provided)
        serializer = ParkingSpotSerializer(spot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Delete the spot
        spot.delete()
        return Response({'message': 'Spot deleted successfully'}, status=204)

# 9. Get Completed Transaction History
@api_view(['GET'])
def transaction_history_api(request):
    # Fetch only sessions that have a time_out value, ordered by most recent first
    completed_sessions = ParkingSession.objects.exclude(time_out__isnull=True).order_by('-time_out')
    serializer = ParkingSessionSerializer(completed_sessions, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
def settings_api(request):
    # Get the first settings object, or create it if it doesn't exist
    setting, created = SystemSetting.objects.get_or_create(id=1)

    if request.method == 'GET':
        # Added str() to prevent JSON serialization errors
        return Response({'hourly_rate': str(setting.hourly_rate)})

    elif request.method == 'POST':
        new_rate = request.data.get('hourly_rate')
        if new_rate is not None:
            setting.hourly_rate = new_rate
            setting.save()
            # Added str() here too
            return Response({'message': 'Rate updated successfully', 'hourly_rate': str(setting.hourly_rate)})
        return Response({'error': 'Invalid rate provided'}, status=400)

@api_view(['PUT'])
def update_spot(request, pk):
    try:
        spot = ParkingSpot.objects.get(pk=pk)
    except ParkingSpot.DoesNotExist:
        return Response(status=404)

    # Update only the spot_number
    spot.spot_number = request.data.get('spot_number', spot.spot_number)
    spot.save()
    return Response({"message": "Spot updated successfully"})


@api_view(['PUT', 'DELETE'])
def manage_single_spot(request, pk):
    try:
        spot = ParkingSpot.objects.get(pk=pk)
    except ParkingSpot.DoesNotExist:
        return Response(status=404)

    if request.method == 'PUT':
        spot.spot_number = request.data.get('spot_number', spot.spot_number)
        spot.save()
        return Response({"message": "Updated"})

    elif request.method == 'DELETE':
        # Optional: Prevent deleting if a car is parked there
        if spot.is_occupied:
            return Response({"error": "Cannot delete an occupied spot"}, status=400)

        spot.delete()
        return Response({"message": "Deleted successfully"}, status=204)