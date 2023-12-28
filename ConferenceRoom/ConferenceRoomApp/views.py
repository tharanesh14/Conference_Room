from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse,HttpResponseRedirect
from .models import Booking, EventRequest, ConferenceRoom
from .forms import BookingForm, RoomAvailabilityForm
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .task import send_overlap_email, allow_overlaps, send_approval_email, send_rejection_email
from ajax_datatable import AjaxDatatableView
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, allowed_user


@login_required(login_url="login")
@allowed_user(allowed_roles=["Staff"])
def staff_page(request):
    events = Booking.objects.all()
    return render(request, "staff_page.html", {'events':events})

# class StaffPageView(AjaxDatatableView):
#     model = Booking
#     show_column_filters = False

#     column_defs = [
#         {'name': 'name', 'visible': True},
#         {'name': 'chair_count', 'visible': True},
#         {'name': 'start_time', 'visible': True},
#         {'name': 'end_time', 'visible': True}, 
#         {'name': 'ac_required', 'visible': True},
#         {'name': 'projector_required', 'visible': True},
#     ]

#     def get(self, request, *args, **kwargs):
#         # Check if the 'draw' parameter is present
#         query_dict = request.GET
#         if 'draw' not in query_dict:
#             return JsonResponse({
#                 'error': 'Draw parameter missing',
#             })

#         # Continue processing the DataTables Ajax request
#         draw = int(query_dict['draw'])
#         # Add any additional processing specific to your DataTable here

#         # Render the HTML page for staff_page view
#         events = Booking.objects.all()
#         return render(request, "staff_page.html", {'events': events})

# Create your views here.


def home(request):
    return render(request, "home.html")


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def calendar(request):
    conference_rooms = ConferenceRoom.objects.all()
    room_id = request.GET.get('room_id')
    events = Booking.objects.all()
    events_query = Booking.objects.all()
    if room_id:
        events_query = events_query.filter(conference_room__id=room_id)
    
    all_events = events_query
    
    form = BookingForm()
    
    is_staff = request.user.is_authenticated and request.user.groups.filter(name__iexact='Staff').exists()
    
    context = {
        "conference_rooms": conference_rooms, 
        "selected_room_id": int(room_id) if room_id else None, 
        "Booking": all_events,
        'form': form,
        'is_staff': is_staff,  
        'events': events,

    }
    return render(request, 'calendar.html', context)


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def all_events(request):
    room_id = request.GET.get('room_id')
    events_query = Booking.objects.all()
    
    if room_id:
        events_query = events_query.filter(conference_room__id=room_id)
    
    events = []

    for event in events_query:
        events.append({
            'title': event.name,
            'start': event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'end': event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'id': event.id,
        })

    return JsonResponse(events, safe=False)


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def all_Booking(request):                                                                                                 
    all_Booking = Booking.objects.all()                                                                                    
    out = []                                                                                                             
    for event in all_Booking:                                                                                             
        out.append_time({                                                                                                     
            'title': event.name,                                                                                         
            'id': event.id,                                                                                              
            'start_time': event.start_time_time.strftime("%m/%d/%Y, %H:%M:%S"),                                                         
            'end_time': event.end_time_time.strftime("%m/%d/%Y, %H:%M:%S"),                                                             
        })                                                                                                               
                                                                                                                      
    return JsonResponse(out, safe=False) 
 

@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
@transaction.atomic
def add_event(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["name"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            conference_room = form.cleaned_data["conference_room"]
            # chair_count = form.cleaned_data["chair_count"]
            user = request.user

            chair_count = request.POST.get("chair_count")
            ac_required = request.POST.get("ac_required") == "on"
            projector_required = request.POST.get("projector_required") == "on"

            is_staff = user.groups.filter(name='Staff').exists()
            allow_overlap = request.POST.get("overlap") == "on" and is_staff

            # Check for overlapping events in the selected conference room
            overlapping_events = Booking.objects.filter(
                Q(conference_room=conference_room) &
                Q(start_time__lt=end_time, end_time__gt=start_time)
            )

            if not allow_overlap and overlapping_events.exists():
                # Check if any of the overlapping events belong to the same user
                user_events = overlapping_events.filter(user=user)
                if user_events.exists():
                    return JsonResponse({"success": False, "message": "Cannot overlap with your own event."})

                event = Booking(
                    name=title,
                    start_time=start_time,
                    end_time=end_time,
                    conference_room=conference_room,
                    user=user,
                    ac_required=ac_required,
                    projector_required=projector_required,
                    chair_count=chair_count,
                )
                event.save()

                # For overlapping events that belong to others, send requests and emails
                for old_event in overlapping_events.exclude(user=user):
                    event_request = EventRequest(
                        requester=user,
                        booking=old_event,
                        overlapping_event=event
                    )
                    event_request.save()
                    send_overlap_email.delay(old_event.user.email, old_event.name)
                    # send_mail(
                    #         'Overlap Request',
                    #         'Your event overlaps with another event. Please review and approve the overlap request.',
                    #         'from@example.com',
                    #         [old_event.user.email],
                    #         fail_silently=False,
                    #     )
                
                return JsonResponse({"success": True})
            
            if allow_overlap:
                # Delete overlapping events that belong to others
                for old_event in overlapping_events.exclude(user=user):
                    old_event.delete()
                
                event = Booking(
                    name=title,
                    start_time=start_time,
                    end_time=end_time,
                    conference_room=conference_room,
                    user=user,
                    ac_required=ac_required,
                    projector_required=projector_required,
                    chair_count=chair_count,
                )
                event.save()
                allow_overlaps.delay(old_event.user.email, old_event.name)

                return JsonResponse({"success": True})

            event = Booking(
                name=title,
                start_time=start_time,
                end_time=end_time,
                conference_room=conference_room,
                user=user,
                ac_required=ac_required,
                projector_required=projector_required,
                chair_count=chair_count,
            )
            event.save()

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "message": "Form validation failed"})

    return JsonResponse({"success": False, "message": "Invalid request"})

 
@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def update(request):
    event_id = request.GET.get("id", None)
    start_time = request.GET.get("start_time", None)
    end_time = request.GET.get("end_time", None)
    title = request.GET.get("title", None)
    
    try:
        event = Booking.objects.get(id=event_id)
        is_staff = request.user.groups.filter(name='Staff').exists()
        if request.user == event.user or is_staff or request.user.is_superuser:
            # Check for overlapping events, excluding the current event
            overlapping_events = Booking.objects.filter(
                Q(start_time__lt=end_time, end_time__gt=start_time) &
                ~Q(id=event_id)
            )
            event.name = title
            event.start_time = start_time
            event.end_time = end_time
            event.save()
            if overlapping_events.exists():
                # Send event approval request to old event owners
                for old_event in overlapping_events:
                    # Check if the old event belongs to another user
                    if old_event.user != event.user:
                        event_request = EventRequest(
                            requester=request.user,
                            booking=old_event,
                            overlapping_event=event
                        )
                        event_request.save()
                        send_overlap_email.delay(old_event.user.email, old_event.name)
                return JsonResponse({'success': True, 'message': 'Overlap request sent to existing event owners.'})
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Event not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def event_details(request, pk):
    event = get_object_or_404(Booking, pk=pk)
    
    # Get the total chair count for the conference room (if available)
    room_chair_count = event.conference_room.number_of_chairs if event.conference_room else 0
    
    # Get the chairs that are already booked for this event
    booked_chairs = event.chair_count
    
    # Calculate the remaining chair count
    remaining_chair_count = room_chair_count - booked_chairs
    
    context = {
        'event': event,
        'room_chair_count': room_chair_count,
        'remaining_chair_count': remaining_chair_count,
        'booked_chairs': booked_chairs,
    }
    
    return render(request, 'event_details.html', context)


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def remove(request):
    id = request.GET.get("id", None)
    event = get_object_or_404(Booking, id=id)
    user = request.user
    is_staff = user.groups.filter(name='Staff').exists()

    # Check if the user is staff or a superuser or if they own the event
    if request.user == event.user or is_staff or request.user.is_superuser:
        event.delete()
        data = {'success': True}
    else:
        data = {'error': 'Unauthorized to delete this event.'}

    return JsonResponse(data)


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def update_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('id')
        title = request.POST.get('name')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        ac_required = request.POST.get("ac_required") == "on"
        projector_required = request.POST.get("projector_required") == "on"
        conference_room_id = request.POST.get('conference_room')
        chair_count = request.POST.get("chair_count")

        try:
            event = Booking.objects.get(id=event_id)
            
            is_staff = request.user.groups.filter(name='Staff').exists()

            if request.user == event.user or is_staff or request.user.is_superuser:
                event.name = title
                event.start_time = start_time
                event.end_time = end_time
                event.ac_required = ac_required
                event.projector_required = projector_required
                event.chair_count = chair_count

                conference_room = ConferenceRoom.objects.get(id=conference_room_id)
                event.conference_room = conference_room
                
                event.save()

                # Check for overlapping events excluding the current event
                overlapping_events = Booking.objects.filter(
                    Q(conference_room=event.conference_room) &
                    Q(start_time__lt=end_time, end_time__gt=start_time) &
                    ~Q(id=event_id)
                )

                if overlapping_events.exists():
                    # Send event approval request to old event owners
                    for old_event in overlapping_events:
                        # Check if the old event belongs to another user
                        if old_event.user != event.user:
                            event_request = EventRequest(
                                requester=request.user,
                                booking=old_event,
                                overlapping_event=event
                            )
                            event_request.save()
                            #send_overlap_email.delay(old_event.user.email, old_event.name)

                    return JsonResponse({'success': True, 'message': 'Overlap request sent to existing event owners.'})

                event.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'Unauthorized'})
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Event not found'})
        except ConferenceRoom.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Conference Room not found'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def event_requests(request):
    user_events = Booking.objects.filter(user=request.user)
    requests = EventRequest.objects.filter(status='pending_approval', booking__in=user_events)
    context = {"requests": requests}
    return render(request, "event_requests.html", context)


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def handle_event_request(request, request_id):
    event_request = get_object_or_404(EventRequest, id=request_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            event_request.approve()

            old_event = event_request.booking
            old_event.delete()
            
            send_approval_email.delay(old_event.user.email, old_event.name)

        elif action == "reject":
            event_request.reject()
            
            new_event=event_request.overlapping_event
            new_event.delete()
            
            send_rejection_email.delay(new_event.user.email, new_event.name)


        return HttpResponseRedirect(reverse("event_requests"))
    else:
        return render(request, "event_request.html", {"event_request": event_request})







@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def finding_page(request):
    form = RoomAvailabilityForm()

    return render(request, 'find_meeting_hall.html', {'form': form})


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
@csrf_exempt
def find_meeting_hall(request):
    if request.method == "POST":
        form = RoomAvailabilityForm(request.POST)
        if form.is_valid():
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            ac_required = form.cleaned_data["ac_required"]
            projector_required = form.cleaned_data["projector_required"]

            booked_meeting_hall = Booking.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            available_meeting_halls = ConferenceRoom.objects.filter(
                id__in=[
                    room.id for room in ConferenceRoom.objects.all()
                    if (
                        room not in booked_meeting_hall and
                        (not ac_required or room.has_ac) and
                        (not projector_required or room.has_projector)
                    )
                ]
            )

            available_room_names = [room.room_name for room in available_meeting_halls]

            return JsonResponse({"available_rooms": available_room_names})

    return JsonResponse({"error": "Invalid request"})


@login_required(login_url="login")
@allowed_user(allowed_roles=["Employee", "Staff"])
def check_room_features(request):
    room_id = request.GET.get('room_id')
    room = ConferenceRoom.objects.filter(id=room_id).first()

    if room:
        return JsonResponse({
            'has_ac': room.has_ac,
            'has_projector': room.has_projector,
            'number_of_chairs': room.number_of_chairs
            
        })
    else:
        return JsonResponse({
            'has_ac': False,
            'has_projector': False,
            'number_of_chairs': 0  
        })


