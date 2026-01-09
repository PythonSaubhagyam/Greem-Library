from django.views import View
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from web_project import TemplateLayout, TemplateHelper  # keep your existing layout logic
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.conf import settings
# from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from django.http import JsonResponse

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('auth-login-basic') 
    

class AuthView(View):
    template_name = "auth_login_basic.html"

    def get(self, request):
        if request.user.is_authenticated:
            # if request.user.role.name == "Admin" and request.user.id in settings.ADMIN_IDS:
            #     return redirect("admin-dashboard")
            return redirect("index")
        
        context = TemplateLayout.init(self, {})
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get("email-username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        context = TemplateLayout.init(self, {})
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })

        if user is not None:
            login(request, user)
            
            # Generate JWT tokens for authenticated user
            # refresh = RefreshToken.for_user(user)
            # access_token = str(refresh.access_token)
            
            token, created = Token.objects.get_or_create(user=user)

            # If the request came via JS (like fetch)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': True,
                    # 'access_token': access_token,
                    # 'refresh_token': str(refresh),
                    'token': token.key,
                    'role': user.role.name,
                    'message': 'Login successful'
                })
                
            # if user.role.name == "Admin" and user.id in settings.ADMIN_IDS:
            #     return redirect("admin-dashboard")
            return redirect("index")  # dashboard or homepage
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': False,
                    'message': 'Invalid username or password'
                })
            context["error"] = "Invalid username or password"
            return render(request, self.template_name, context)




class RegisterView(View):
    template_name = "auth_register_basic.html"

    def get(self, request):
        context = TemplateLayout.init(self, {})
        context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        terms = request.POST.get("terms")

        context = TemplateLayout.init(self, {})
        context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)

        if not terms:
            context["error"] = "You must agree to the terms and conditions."
            return render(request, self.template_name, context)

        if User.objects.filter(username=username).exists():
            context["error"] = "Username already exists."
            return render(request, self.template_name, context)

        if User.objects.filter(email=email).exists():
            context["error"] = "Email already registered."
            return render(request, self.template_name, context)

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)  # Auto-login after registration
        return redirect("index")

