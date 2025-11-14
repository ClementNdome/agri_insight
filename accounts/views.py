from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views import View
from django.contrib import messages
from .models import User
from .forms import SignupForm


class SignupView(CreateView):
    """User signup view"""
    model = User
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('landing')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Account created successfully! Welcome to Agri Insight.')
        return response


class CustomLoginView(LoginView):
    """Custom login view with remember me functionality"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            # Set session to expire when browser closes
            self.request.session.set_expiry(0)
        else:
            # Set session to expire in 2 weeks
            self.request.session.set_expiry(1209600)
        return super().form_valid(form)


class CustomLogoutView(View):
    """Custom logout view that handles both GET and POST requests"""
    
    def get(self, request):
        """Show logout confirmation page"""
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'accounts/logout.html')
    
    def post(self, request):
        """Perform logout"""
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been logged out successfully.')
        return redirect('landing')

