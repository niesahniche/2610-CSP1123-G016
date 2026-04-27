from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

 
 
# ------- 2 Hardcoded Users -------
HARDCODED_USERS = [
    {
        "name": "Khairin Aqilah",
        "username": "qyla",
        "email": "khairin.aqilah@gmail.com",
        "password": "2809",
    },
    {
        "name": "Khairol Zharfan",
        "username": "kai",
        "email": "khai.zhar@gmail.com",
        "password": "6311",
    },
]

def create_hardcoded_users():
    """Creates the hardcoded users since database don't exist yet."""
    for u in HARDCODED_USERS:
        if not User.objects.filter(username=u["username"]).exists():
            new_user = User.objects.create_user(
                username=u["username"],
                email=u["email"],
                first_name=u["name"],
            )
            new_user.set_password(u["password"])
            new_user.save()

# Auto-create hardcoded users when the app loads
try:
    create_hardcoded_users()
except Exception:
    pass
# ---------------------------------------------------  

def find_hardcoded_user(email, password):
    """Returns matching hardcoded user dict, or None."""
    for u in HARDCODED_USERS:
        if u["email"] == email and u["password"] == password:
            return u
    return None
         

def signup(request):
    if request.user.is_authenticated:
        return redirect("home")  
 
    if request.method == "POST":
        # Check if submitted details match one of the hardcoded users
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password1", "").strip() # matches name="password1" in signup.html
        matched = find_hardcoded_user(email, password)
        
        if matched:
            try:
                user = User.objects.get(username=matched["username"])
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Welcome, {matched['name']}! You're now signed in.")
                return redirect("home")
            except User.DoesNotExist:
                messages.error(request, "Account setup incomplete. Please contact support.")
        else:
            messages.error(request, "These details do not match any registered account.")
 
    return render(request, "signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    
    if request.method == "POST":
        email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        matched = find_hardcoded_user(email, password)

        if matched:
            try:
                user = User.objects.get(username=matched["username"])
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Welcome back, {matched['name']}!")
                return redirect("home")
            except User.DoesNotExist:
                messages.error(request, "Account setup incomplete. Please contact support.")
        else:
            messages.error(request, "Invalid email or password.")
 
    return render(request, "login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("login")
    # If someone visits /logout/ via GET, redirect to home
    return redirect("home")


@login_required
def home(request):
    return render(request, "home.html", {"user": request.user}) #passes user to template

@login_required
def profile(request):
    return render(request, "user_profile.html", {"user": request.user})