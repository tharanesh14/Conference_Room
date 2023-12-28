
from celery import shared_task
from django.core.mail import send_mail
from .models import Booking

@shared_task
def send_overlap_email(user_email, event_title):
    print(user_email,event_title)
    subject = 'Overlap Request'
    message = f'Your Meeting ({event_title}) overlaps with another meeting. Please check your request.'
    from_email = 'your_email@example.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    
@shared_task
def allow_overlaps(user_email, event_title):
    print(user_email,event_title)
    subject = 'Staff User Overlaped with Your Meeting '
    message = f'Your Meeting ({event_title}) has been overlaped with another meeting.'
    from_email = 'your_email@example.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    
    
@shared_task
def send_approval_email(user_email, event_name):
    subject = 'Meeting Approval'
    message = f'Your Meeting "{event_name}" has been approved.'
    from_email = 'your_email@example.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list)

@shared_task
def send_rejection_email(user_email, event_name):
    subject = 'Meeting Rejection'
    message = f'Your Meeting "{event_name}" has been rejected.'
    from_email = 'your_email@example.com'
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)
