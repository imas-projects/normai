from django.shortcuts import render, redirect
from django.urls import reverse
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import TemplateView
from django.http import JsonResponse
from audits.models import Area
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
# Create your views here.


# Páginas de inicio según grupos usuarios.
'''
class AuditorVentasDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView): 
    template_name = "mistemplates/auditor_ventas-dashboard.html"
    permission_denied_message = "Este usuario no tiene acceso a esta página"

    def test_func(self):
        # print("test") #debug
        return self.request.user.groups.filter(name='auditor_ventas').exists()

class AuditablesVentasDashboardView(LoginRequiredMixin, UserPassesTestMixin,TemplateView):
    template_name = "mistemplates/auditables_ventas-dashboard.html"
    permission_denied_message = "Este usuario no tiene acceso a esta página"

    def test_func(self):
        # print("test") #debug
        return self.request.user.groups.filter(name='auditables_ventas').exists()
'''

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

@csrf_protect
def authentication_sign_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.POST.get("next") or reverse(f"authentication:wellcome_view")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            #print("sesion iniciada") #debug
            return redirect(next_url)
        else:
            return render(request, "mistemplates/authentication-sign-in.html", {"error": "Usuario o contraseña incorrectos"})
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
'''
#sign in usando java y json
@csrf_exempt
def authentication_sign_in(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(username=username, password=password)

            all_groups = Group.objects.all()

            if user is not None:
                login(request, user)
                print("El usuario existe")
                print(f"Sesion iniciada por: {user}")

                if user.is_superuser == True:
                    print("superusuario")
                    return JsonResponse({'success': True, 'redirect_url': reverse(f"admin:index")})
                else:
                    user_groups = Group.objects.get(id=user.groups.first().id)
                    print("El usuario esta en un grupo")
                    return JsonResponse({'success': True, 'redirect_url': reverse(f"authentication:wellcome_view")})
                    #return JsonResponse({'success': True, 'redirect_url': reverse(f"pages:pages_normai_landing")})
                    #return JsonResponse({'success': True, 'redirect_url': reverse(f"authentication:{user_groups.name}_dashboard_view")})

                #return JsonResponse({'success': True})
            else:
                print("el usuario no existe")
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})    
    return render(request, "mistemplates/authentication-sign-in.html")

'''