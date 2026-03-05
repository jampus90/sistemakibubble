from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework_simplejwt.tokens import RefreshToken

def index(request):
    return render(request, 'base.html')

def login(request):
    user_list = User.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            refresh = RefreshToken.for_user(user)
            return render(request, 'base.html', {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            })
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password', 'user_list': user_list})
    return render(request, 'login.html', {'user_list': user_list})

def is_admin(user):
    return user.is_staff

@login_required(login_url='login')
@user_passes_test(is_admin)
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        return redirect('index')
    
    return render(request, 'register.html')
