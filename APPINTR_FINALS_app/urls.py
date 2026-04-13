from django.urls import path
from . import views

urlpatterns = [
    path('spots/available/', views.get_available_spots, name='available-spots'),
    path('sessions/active/', views.get_active_sessions, name='active-sessions'),
    path('check-in/', views.check_in, name='check-in'),
    path('check-out/<int:session_id>/', views.check_out, name='check-out'),
]