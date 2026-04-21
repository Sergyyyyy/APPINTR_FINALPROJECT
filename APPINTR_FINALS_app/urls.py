from django.urls import path
from . import views

urlpatterns = [
    path('spots/available/', views.get_available_spots, name='available-spots'),
    path('sessions/active/', views.get_active_sessions, name='active-sessions'),
    path('check-in/', views.check_in, name='check-in'),
    path('check-out/<int:session_id>/', views.check_out, name='check-out'),
    path('dashboard/metrics/', views.get_dashboard_metrics, name='dashboard-metrics'),
    path('dashboard/recent/', views.get_recent_activity, name='dashboard-recent'),

    # 1. FIX: Changed 'manage-spots/' to 'spots/' to match your JS fetch
    path('spots/', views.manage_spots_api, name='manage-spots-list-api'),

    # 2. FIX: Consolidate the detail view (Edit/Delete) into ONE path
    # Make sure 'manage_single_spot' is the view that handles BOTH PUT and DELETE
    path('spots/<int:pk>/', views.manage_single_spot, name='manage-spot-detail-api'),

    path('transactions/', views.transaction_history_api, name='transaction-history-api'),
    path('settings/', views.settings_api, name='settings-api'),

    # REMOVED the duplicate 'manage-spots/<int:pk>/' to keep it clean
]