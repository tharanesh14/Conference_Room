from django import template



register = template.Library()

@register.filter
def is_staff_group(user):
    return user.groups.filter(name='Staff').exists()