from django.db import models
from django.contrib.auth.models import User


class ConferenceRoom(models.Model):
    room_name = models.CharField(max_length=255, unique=True)
    number_of_chairs = models.PositiveIntegerField()
    has_ac = models.BooleanField(default=False)
    has_projector = models.BooleanField(default=False)

    def __str__(self):
        return self.room_name


class Booking(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    conference_room = models.ForeignKey(ConferenceRoom, on_delete=models.CASCADE,default=None)
    name = models.CharField(max_length=255, null=True, blank=True)
    chair_count = models.PositiveIntegerField(default=1, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    ac_required = models.BooleanField(default=False)
    projector_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class EventRequest(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending_approval')
    overlapping_event = models.OneToOneField('Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='overlapping_request')

    def approve(self):
        self.status = 'approved'
        self.booking.status = 'approved'
        self.booking.save()
        self.save()
        
        # self.status = 'approved'
        
        # try:
        #     if self.booking:
        #         self.booking.delete()  # Delete the old event
        # except ValueError:
        #     print('utc')
        #     pass  # Ignore the ValueError
        # self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()
        # self.status = 'rejected'
        # try:
        #     if self.overlapping_event:
        #         self.overlapping_event.delete()  # Delete the overlapping event
        #         print("old delete")
        # except ValueError:
        #     print("ve error")
        #     pass 
        # self.booking.status = 'rejected'
        # self.booking.save()
        # self.save()



