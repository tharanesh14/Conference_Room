from django.contrib import admin
from .models import ConferenceRoom, Booking, EventRequest

admin.site.register(ConferenceRoom)
admin.site.register(Booking)
admin.site.register(EventRequest)