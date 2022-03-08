from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from users import views

# Create your views here.
def home(request):

	if request.user.is_authenticated:
		return render(request, 'nets/home.html')
	else:
		return render(request, 'nets/home.html')
		# TODO: Change it so that it redirects to login page
		#redirect(auth_views.LoginView)
		