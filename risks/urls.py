from django.urls import path
from .views import create_risk, edit_risk_identification, edit_risk_evaluation, edit_risk_treatment, edit_contingency_plan, edit_reevaluation
from .views import generate_risks_pdf, add_risk_identification, add_risk_evaluation, add_risk_treatment, add_contingency_plan, add_reevaluation, get_controls_suggestions, get_ranges_suggestions, get_level_suggestions, get_treatment_suggestions
from . import views


app_name = 'risks'

urlpatterns = [
  path('', create_risk, name='risks'),
  path('download-risks-pdf/<str:area_name>/', generate_risks_pdf, name='download_risks_pdf'),
  path('add-risk-identification/', add_risk_identification, name='add_risk_identification'),
  path('get_suggestions/', views.get_suggestions, name='get_suggestions'),
  path('add-risk-evaluation/', add_risk_evaluation, name='add_risk_evaluation'),
  path('get-controls-suggestions/', get_controls_suggestions, name='get_controls_suggestions'),
  path('get-ranges-suggestions/', get_ranges_suggestions, name='get_ranges_suggestions'),
  path('get-level-suggestions/', get_level_suggestions, name='get_level_suggestions'),
  path('add-risk-treatment/', add_risk_treatment, name='add_risk_treatment'),
  path('get-treatment-suggestions/', get_treatment_suggestions, name='get_treatment_suggestions'),
  path('add-contingency-plan/', add_contingency_plan, name='add_contingency_plan'),
  path('add-reevaluation/', add_reevaluation, name='add_reevaluation'),
  path('edit-risk-identification/<int:risk_id>/', edit_risk_identification, name='edit-risk-identification'),
  path('edit-risk-evaluation/<int:risk_id>/', edit_risk_evaluation, name='edit-risk-evaluation'),
  path('edit-risk-treatment/<int:risk_id>/', edit_risk_treatment, name='edit-risk-treatment'),
  path('edit-contingency-plan/<int:risk_id>/', edit_contingency_plan, name='edit-contingency-plan'),
  path('edit-reevaluation/<int:risk_id>/', edit_reevaluation, name='edit-reevaluation'),
  ]
