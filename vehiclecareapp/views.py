from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Max
from django.core.mail import send_mail  # <--- Added missing import
from django.conf import settings        # <--- Added missing import
import google.generativeai as genai

from .models import MaintenanceRecord

# Configure Gemini API
genai.configure(api_key="AIzaSyCzRSc5bq7zF1NswvrWkA4kXsN_MsfY_XQ")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password")
    return render(request, "vehiclecareapp/index.html")

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')
        User.objects.create_user(username=email, email=email, password=password)
        return redirect('login')
    return render(request, "vehiclecareapp/signup.html")

@login_required(login_url='login')
def dashboard_view(request):
    records = MaintenanceRecord.objects.filter(user=request.user).order_by('-date')
    unique_vehicles = records.values('vehicle_brand', 'vehicle_model', 'vehicle_type').distinct()
    
    vehicles = []
    
    for v in unique_vehicles:
        brand = v['vehicle_brand']
        model = v['vehicle_model']
        v_type = v['vehicle_type']
        
        car_records = records.filter(vehicle_brand=brand, vehicle_model=model)
        max_reading_query = car_records.aggregate(Max('odometer_reading'))
        current_odo = max_reading_query['odometer_reading__max'] or 0
        
        # --- OIL ---
        last_oil = car_records.filter(maintenance_type='Oil Change').first()
        oil_interval = 3000 if v_type == 'Bike' else 10000
        
        if last_oil:
            km_since = current_odo - last_oil.odometer_reading
            oil_life = max(0, min(100, int(100 - (km_since / oil_interval * 100))))
            next_km = max(0, oil_interval - km_since)
            oil_msg = f"Next change in {next_km} km"
        else:
            oil_life = 0
            oil_msg = "No record found"

        # --- BRAKE ---
        last_brake = car_records.filter(maintenance_type='Brake').first()
        brake_interval = 15000 if v_type == 'Bike' else 30000
        
        if last_brake:
            km_since = current_odo - last_brake.odometer_reading
            brake_life = max(0, min(100, int(100 - (km_since / brake_interval * 100))))
            brake_msg = "Inspection Recommended" if brake_life < 30 else "Condition Good"
        else:
            brake_life = 0
            brake_msg = "No record found"

        vehicles.append({
            'brand': brand, 'model': model, 'type': v_type,
            'icon': '🏍️' if v_type == 'Bike' else '🚗',
            'oil_life': oil_life, 'oil_msg': oil_msg,
            'brake_life': brake_life, 'brake_msg': brake_msg,
        })

    context = {'records': records, 'vehicles': vehicles}
    return render(request, "vehiclecareapp/dashboard.html", context)

@login_required
def chatbot_response(request):
    user_message = request.GET.get('message', '').lower().strip()
    is_bike = any(w in user_message for w in ['bike', 'motorcycle', 'scooter'])
    is_car = any(w in user_message for w in ['car', 'sedan', 'suv'])
    
    response_text = ""

    # TIER 1: YOUR RULES
    if 'oil' in user_message:
        if is_bike: response_text = "For bikes, oil change is every 2,500-3,000 km."
        elif is_car: response_text = "For cars, oil change is every 8,000-10,000 km."
        else: response_text = "Oil changes: ~10k km for cars, ~3k km for bikes."
    elif 'brake' in user_message:
        if is_bike: response_text = "Bike brake pads last 10k-15k km."
        elif is_car: response_text = "Car brake pads last 30k-50k km."
        else: response_text = "Brake pads vary by vehicle type."
    elif 'battery' in user_message:
        response_text = "Check battery every 30,000 km or 3-4 years."
    elif 'air filter' in user_message:
        if is_bike: response_text = "Bike air filters: change every 8,000-10,000 km."
        elif is_car: response_text = "Car air filters: change every 15,000-20,000 km."
        else: response_text = "Air filter: <20k km for cars, <10k km for bikes."
    elif any(w in user_message for w in ['hi', 'hello']):
        response_text = "Hello! Ask me about maintenance schedules."
        
    # TIER 2: GEMINI API
    if not response_text:
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("You are a vehicle mechanic assistant. Answer concisely: " + user_message)
            response_text = response.text
        except Exception as e:
            print(f"\n======== GEMINI ERROR ========\n{e}\n==============================\n")
            response_text = "I'm having trouble connecting. (Check server terminal for error details)"

    return JsonResponse({'response': response_text})

@login_required(login_url='login')
def add_maintenance(request):
    if request.method == "POST":
        vehicle_brand = request.POST.get("vehicle_brand")
        vehicle_model = request.POST.get("vehicle_model")
        vehicle_type = request.POST.get("vehicle_type")
        maintenance_type = request.POST.get("maintenance_type")
        odo_str = request.POST.get("odometer_reading")
        odometer_reading = int(odo_str) if odo_str else 0
        date = request.POST.get("date")

        car_intervals = {'Oil Change': 10000, 'Brake': 30000, 'Tire Rotation': 10000, 'Battery': 30000, 'Air filter': 20000}
        bike_intervals = {'Oil Change': 3000, 'Brake': 15000, 'Chain': 500, 'Battery': 30000, 'Air filter': 10000}

        interval = bike_intervals.get(maintenance_type, 3000) if vehicle_type == "Bike" else car_intervals.get(maintenance_type, 10000)
        next_service = odometer_reading + interval
        
        # 1. Save Record
        MaintenanceRecord.objects.create(
            user=request.user, vehicle_brand=vehicle_brand, vehicle_model=vehicle_model,
            vehicle_type=vehicle_type, maintenance_type=maintenance_type,
            odometer_reading=odometer_reading, next_service_km=next_service, date=date
        )

        # 2. Send Email
        if request.user.email:
            subject = f"VehicleCare+: New Service for {vehicle_brand} {vehicle_model}"
            message = (
                f"Hi {request.user.username},\n\n"
                f"New service record added:\n"
                f"Vehicle: {vehicle_brand} {vehicle_model}\n"
                f"Service: {maintenance_type}\n"
                f"Odometer: {odometer_reading} km\n"
                f"Next Due: {next_service} km\n\n"
                f"Drive Safe,\nVehicleCare+ Team"
            )
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [request.user.email]
            
            try:
                send_mail(subject, message, email_from, recipient_list)
                print(f"Email sent successfully to {request.user.email}")
            except Exception as e:
                print(f"Email Failed: {e}")

    return redirect('dashboard')

@login_required(login_url='login')
def delete_record(request, record_id):
    record = get_object_or_404(MaintenanceRecord, id=record_id, user=request.user)
    record.delete()
    return redirect('dashboard')

def logout_view(request):
    logout(request)
    return redirect('login')