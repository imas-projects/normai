"""velzon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth.decorators import login_required
from .views import MyPasswordChangeView, MyPasswordSetView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Dashboard
    path('dashboards/',include('dashboards.urls')),
    # Apps
    path('apps/',include('apps.urls')),
    # Layouts
    path('layouts/',include('layouts.urls')),
    # Components
    path('components/',include('components.urls')),
    # Pages
    path('',include('pages.urls')),
    path(
        "account/password/change/",
        login_required(MyPasswordChangeView.as_view()),
        name="account_change_password",
    ),
    path(
        "account/password/set/",
        login_required(MyPasswordSetView.as_view()),
        name="account_set_password",
    ),
    # All Auth 
    path('account/', include('allauth.urls')),
    # Mis apps
    path('company/', include('company.urls')),
    path('communications/', include('communications.urls')),
    path('risks/', include('risks.urls')),
    path('authentication/', include('authentication.urls')),
    path('audits/', include('audits.urls')),
    path('processes/', include('processes.urls')),
    path('ai_functions/', include('ai_functions.urls')),
    
]

# Personalizar Página Administrador
admin.site.site_header = "NormAI"
admin.site.site_title = "NormAI"
admin.site.index_title = "Página de Administrador"


if settings.DEBUG:
    # Para archivos estáticos
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Para archivos de media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)