from django.urls import path
from .views import create_risk
from .views import generate_risks_pdf, get_risk_data, update_risk
from . import views

app_name = 'risks'

urlpatterns = [
    path("get-risk-data/<int:risk_id>/", get_risk_data, name="get-risk-data"),
    path("update-risk/<int:risk_id>/step-<int:step>/", update_risk, name="update-risk-step"),
    path('', views.create_risk, name='risks'),
    path('download-risks-pdf/<str:department_name>/', generate_risks_pdf, name='download_risks_pdf'),
    path("save-risk-step/<int:step>/", views.save_risk_step, name="save-risk-step")
  ]
