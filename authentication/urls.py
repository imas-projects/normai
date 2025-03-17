from django.urls import path
from . import views
from . views import AuditorVentasDashboardView, AuditablesVentasDashboardView 

app_name = 'authentication'

urlpatterns = [
    path('wellcome/', views.wellcome_view, name='wellcome_view'),
    path('sign-up/',views.authentication_sign_up,name='authentication_sign_up'),
    path('sign-in/',views.authentication_sign_in,name='authentication_sign_in'),
    path('log-out/',views.authentication_log_out,name='authentication_log_out'),

    path('log-out/',views.authentication_log_out,name='authentication_log_out'),
    path('ventas-auditor/', AuditorVentasDashboardView.as_view(), name='auditor_ventas_dashboard_view'),
    path('ventas-auditables/',views.AuditablesVentasDashboardView.as_view(), name='auditables_ventas_dashboard_view'),
    #path('prueba/',views.prueba_sign_up,name='prueba'),
]


