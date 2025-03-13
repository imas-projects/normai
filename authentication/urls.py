from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('wellcome/', views.wellcome_view, name='wellcome_view'),
    path('sign-up/',views.authentication_sign_up,name='authentication_sign_up'),
    path('sign-in/',views.authentication_sign_in,name='authentication_sign_in'),
    path('log-out/',views.authentication_log_out,name='authentication_log_out'),
]


