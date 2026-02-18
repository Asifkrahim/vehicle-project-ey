from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Max, Sum
from django.core.mail import send_mail
from django.conf import settings
import google.generativeai as genai

from .models import MaintenanceRecord

# ==============================================================================
# 🔑 API KEY CONFIGURATION
# ==============================================================================
# Ensure your key is valid at: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = "AIzaSyB0hq6ReqzNWBQtahrew7mVFpwBLQz3agw"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"⚠️ API CONFIG ERROR: {e}")

# --- GLOBAL INTERVAL CONFIGURATION ---
CAR_INTERVALS = {
    'Oil Change': 10000, 'Brake Inspection': 30000, 'Tire Rotation': 10000,
    'Air Filter': 20000, 'Cabin Filter': 20000, 'Coolant Flush': 50000,
    'Spark Plugs': 50000, 'Transmission Fluid': 60000, 'Battery Check': 30000,
    'Timing Belt': 100000, 'General Service': 10000
}

BIKE_INTERVALS = {
    'Oil Change': 3000, 'Brake Inspection': 15000, 'Chain Lube': 500,
    'Chain Adjustment': 1000, 'Air Filter': 10000, 'Coolant Flush': 20000,
    'Spark Plugs': 15000, 'Valve Clearance': 25000, 'Battery Check': 15000,
    'Tire Check': 5000, 'General Service': 3000
}

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
    total_expense = records.aggregate(Sum('cost'))['cost__sum'] or 0
    unique_plate_numbers = records.values_list('vehicle_number', flat=True).distinct()
    
    vehicles = []
    
    for plate in unique_plate_numbers:
        car_records = records.filter(vehicle_number=plate)
        latest_record = car_records.first()
        brand = latest_record.vehicle_brand
        model = latest_record.vehicle_model
        v_type = latest_record.vehicle_type
        
        intervals = BIKE_INTERVALS if v_type == 'Bike' else CAR_INTERVALS
        max_reading_query = car_records.aggregate(Max('odometer_reading'))
        current_odo = max_reading_query['odometer_reading__max'] or 0
        
        def calculate_health(m_type):
            last_rec = car_records.filter(maintenance_type__icontains=m_type).order_by('-date', '-odometer_reading').first()
            limit = intervals.get(m_type, 10000)
            
            if last_rec:
                km_since = max(0, current_odo - last_rec.odometer_reading)
                life = max(0, min(100, int(100 - (km_since / limit * 100))))
                
                # --- FIX: Display the actual "Due at X km" reading ---
                # We use the 'next_service_km' stored in the database record
                target_odo = last_rec.next_service_km 
                msg = f"Due at {target_odo} km"
            else:
                life, msg = 0, "No Record Found"
            return life, msg

        oil_life, oil_msg = calculate_health('Oil Change')
        brake_life, brake_msg = calculate_health('Brake Inspection')
        air_life, air_msg = calculate_health('Air Filter')
        coolant_life, coolant_msg = calculate_health('Coolant Flush')

        vehicles.append({
            'number': plate, 'brand': brand, 'model': model, 'type': v_type,
            'icon': '🏍️' if v_type == 'Bike' else '🚗', 'current_odo': current_odo,
            'oil_life': oil_life, 'oil_msg': oil_msg,
            'brake_life': brake_life, 'brake_msg': brake_msg,
            'air_life': air_life, 'air_msg': air_msg,
            'coolant_life': coolant_life, 'coolant_msg': coolant_msg,
        })

    context = {'records': records, 'vehicles': vehicles, 'total_expense': total_expense}
    return render(request, "vehiclecareapp/dashboard.html", context)

@login_required
def chatbot_response(request):
    """
    PURE AI RESPONSE
    Using 'gemini-1.5-flash' which is the current stable model.
    """
    user_message = request.GET.get('message', '').strip()
    
    if not user_message:
        return JsonResponse({'response': "I'm listening..."})

    try:
        # 1. Initialize Model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 2. System Instruction
        prompt = (
            "You are an expert mechanic assistant for VehicleCare+. "
            "Answer the user's question concisely (2-3 sentences max). "
            "Do NOT use markdown (no bold text). "
            f"\n\nUser Question: {user_message}"
        )
        
        # 3. Generate
        response = model.generate_content(prompt)
        
        # 4. Success?
        if response and response.text:
            cleaned_text = response.text.replace('*', '').strip()
            return JsonResponse({'response': cleaned_text})
        else:
            return JsonResponse({'response': "AI connected but returned no text."})

    except Exception as e:
        # Debugging: Print real error to terminal
        print(f"\n❌ GEMINI ERROR DETAILS: {e}\n")
        
        # Friendly UI Error
        if "404" in str(e):
            return JsonResponse({'response': "Error: Model not found. Please run 'pip install --upgrade google-generativeai' in your terminal."})
        elif "429" in str(e):
            return JsonResponse({'response': "Error: Too many requests. Please wait a moment."})
        else:
            return JsonResponse({'response': "Connection Error. Check terminal for details."})

@login_required(login_url='login')
def add_maintenance(request):
    if request.method == "POST":
        vehicle_brand = request.POST.get("vehicle_brand", "").strip().title()
        vehicle_model = request.POST.get("vehicle_model", "").strip().title()
        raw_number = request.POST.get("vehicle_number", "").strip().upper()
        vehicle_number = "".join(raw_number.split()) 
        vehicle_type = request.POST.get("vehicle_type", "").strip().capitalize()
        maintenance_type = request.POST.get("maintenance_type")
        odo_str = request.POST.get("odometer_reading")
        odometer_reading = int(odo_str) if odo_str else 0
        date = request.POST.get("date")
        
        cost_str = request.POST.get("cost")
        cost = float(cost_str) if cost_str else 0.0

        if vehicle_type == "Bike":
            interval = BIKE_INTERVALS.get(maintenance_type, 3000) 
        else:
            interval = CAR_INTERVALS.get(maintenance_type, 10000) 

        next_service = odometer_reading + interval
        
        MaintenanceRecord.objects.create(
            user=request.user, vehicle_brand=vehicle_brand, vehicle_model=vehicle_model,
            vehicle_number=vehicle_number, vehicle_type=vehicle_type, 
            maintenance_type=maintenance_type, odometer_reading=odometer_reading, 
            next_service_km=next_service, date=date, cost=cost 
        )

        if request.user.email:
            subject = f"VehicleCare+: Service Added for {vehicle_number}"
            message = (
                f"Hi {request.user.username},\n\nService Record Saved:\n"
                f"Vehicle: {vehicle_brand} {vehicle_model} ({vehicle_number})\n"
                f"Service: {maintenance_type}\nCost: ₹{cost}\n"
                f"Odometer: {odometer_reading} km\nNext Due: {next_service} km\n\n"
                f"Drive Safe,\nVehicleCare+ Team"
            )
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [request.user.email]
            try:
                send_mail(subject, message, email_from, recipient_list)
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