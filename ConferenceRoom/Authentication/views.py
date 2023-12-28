from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import Group
from .decorators import unauthenticated_user,allowed_user
from .forms import CreateUserForm

# Create your views here.
@unauthenticated_user
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request,username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('calendar')
        else:
            messages.info(request,"Username or Password is Incorrect!")
            return render(request,"login.html")
    return render(request,"login.html")

def logout(request):
    auth_logout(request)
    return redirect("register")

def register(request):
    login(request)
    if request.user.is_authenticated:
        return redirect('calendar')
    else:
        if request.method == "POST":
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                selected_group = form.cleaned_data.get('user_group')
                if selected_group:
                    group, created = Group.objects.get_or_create(name=selected_group)
                    user.groups.add(group)
                messages.success(request, "Account was created successfully")
                return redirect('login')
        else:
            form = CreateUserForm()
    return render(request, "login.html", {'form': form})