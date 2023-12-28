from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('home',views.home, name='home'),
    path('calendar',views.calendar, name='calendar'),
    path('all_events', views.all_events, name='all_events'), 
    path('add_event', views.add_event, name='add_event'), 
    path('update', views.update, name='update'),
    path('remove', views.remove, name='remove'),
    path('update_event', views.update_event, name='update_event'),
    path('event_requests', views.event_requests, name='event_requests'),
    path('app/handle_event_request/<int:request_id>/', views.handle_event_request, name='handle_event_request'),
    path('finding_page/', views.finding_page, name='finding_page'),
    path('find_meeting_hall/', views.find_meeting_hall, name='find_meeting_hall'),
    path('check_room_features/', views.check_room_features, name='check_room_features'),
    path('event_details/<int:pk>',views.event_details, name='event_details'),
    path('staff_page/',views.staff_page,name="staff_page"),
    # path('ajax_table/',views.StaffPageView.as_view(),name="ajax_table"),
]