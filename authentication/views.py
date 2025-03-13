from django.shortcuts import render, redirect
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
# Create your views here.

@csrf_exempt
def authentication_sign_up(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            new_user = User.objects.create_user(
                first_name = data.get('firstname'),
                last_name = data.get('lastname'),
                username = data.get('username'),
                email = data.get('useremail'),
                password = data.get('password'),
                #groups = data.get(''),
                #user_permissions = data.get(''),
                #is_staff = data.get(''),
                is_active=True 
                #data_joined = data.get(''),
            )
            # Asegúrate de que el usuario esté activo
        
            print("Usuario creado correctamente")
            return JsonResponse({'success': True}) 
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})    
    return render(request, "mistemplates/authentication-sign-up.html")

@csrf_exempt
def authentication_sign_in(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            username = data.get('username')
            password = data.get('password')
            
            # Comprobaciones
            #print(f"Username: {username}, Password: {password}")
            #usuario = User.objects.get(username=username)
            #print(f"Esta activo?: {usuario.is_active}")
            #print(f"Contraseña usable?: {usuario.has_usable_password()}")
            #print(f"Contraseña correcta?: {usuario.check_password(password)}")

            user = authenticate(username=username, password=password)
            print(user)

            if user is not None:
                login(request, user)
                print("el usuario existe")
                if request.user.is_authenticated:
                    print(f"Sesion iniciada por: {user}")
                    return JsonResponse({'success': True})
                else:
                    print(f"Sesion no iniciada")
            else:
                print("el usuario no existe")
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})    
    return render(request, "mistemplates/authentication-sign-in.html")

def authentication_log_out(request):
    logout(request)
    print("sesion cerrada")
    return render(request, "mistemplates/authentication-log-out.html")