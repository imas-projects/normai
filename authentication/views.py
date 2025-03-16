from django.shortcuts import render, redirect
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from audits.models import Area
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
# Create your views here.

@csrf_exempt
def authentication_sign_up(request):
    all_groups = list(Group.objects.all().values('id', 'name'))

    context = {
        'all_groups' : all_groups,
    }

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            group = data.get('group')
            new_user = User.objects.create_user(
                first_name = data.get('firstname'),
                last_name = data.get('lastname'),
                username = data.get('username'),
                email = data.get('useremail'),
                password = data.get('password'),
                #groups = data.get('group'),
                #user_permissions = data.get(''),
                #is_staff = data.get(''),
                is_active=True 
                #data_joined = data.get(''),
            )
            new_user.groups.set(group)

            print("Usuario creado correctamente")
            return JsonResponse({'success': True}) 
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})    
    return render(request, "mistemplates/authentication-sign-up.html",context)

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

######################## Usuario ########################
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User 

@login_required
def wellcome_view(request):
    return render(request,"mistemplates/wellcome-page.html")

'''
def prueba_sign_up(request):
    # Inicializar formularios
    form_sign_up = UserSignUp()

    if request.method == "POST":
        if form_sign_up.is_valid():
            new_user = User.objects.create_user(
                first_name = form_sign_up.get('first_name'),
                last_name = form_sign_up.get('last_name'),
                username = form_sign_up.get('username'),
                email = form_sign_up.get('email'),
                password = form_sign_up.get('password'),
                groups = form_sign_up.group.get('groups'),
                #user_permissions = data.get(''),
                #is_staff = data.get(''),
                is_active = True 
            )
    context = {
       'form' : form_sign_up,
    }
    return render(request, "mistemplates/form-sign-up.html", context)'
'''