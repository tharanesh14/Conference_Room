from django import forms
from .models import Booking, ConferenceRoom

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'start_time', 'end_time', 'conference_room']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'name', 'style': 'border: 1px solid #ced4da;'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'id': 'start_time', 'style': 'border: 1px solid #ced4da;'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'id': 'end_time', 'style': 'border: 1px solid #ced4da;'}),
            'conference_room': forms.Select(attrs={'class': 'form-control', 'id': 'conference_room', 'style': 'border: 1px solid #ced4da;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the selected conference room from the form's initial data
        selected_room = self.initial.get('conference_room')

        if selected_room:
            # Fetch the number_of_chairs value for the selected conference room
            number_of_chairs = ConferenceRoom.objects.get(id=selected_room.id).number_of_chairs

            # Update the max attribute of the chair_count field
            self.fields['chair_count'].widget.attrs['max'] = number_of_chairs
        
class RoomAvailabilityForm(forms.Form):
    start_time = forms.DateTimeField(
        label="Start Time",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'style': 'border: 1px solid #ced4da;'}),
    )
    end_time = forms.DateTimeField(
        label="End Time",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'style': 'border: 1px solid #ced4da;'}),
    )
    ac_required = forms.BooleanField(
        label="AC Required",
        required=False,  # This makes it optional
        widget=forms.CheckboxInput(attrs={'class': 'form-style-check-input', 'style': 'border: 1px solid #ced4da;'}),
    )
    projector_required = forms.BooleanField(
        label="Projector Required",
        required=False,  # This makes it optional
        widget=forms.CheckboxInput(attrs={'class': 'form-style-check-input', 'style': 'border: 1px solid #ced4da;'}),
    )