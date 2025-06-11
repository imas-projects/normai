from django.urls import path
from . import views

app_name = 'processes'

urlpatterns = [
    path('', views.list_processes, name='list_processes'),
    path('create-process/', views.create_process, name='create_process'),
    path('edit-process/<int:id>/', views.edit_process, name='edit_process'),
    path('update-process/', views.update_process, name='update_process'),
    path('get-process/<int:id>/', views.get_process, name='get_process'),
    path('load-process-form-options/', views.load_form_options, name='load_form_options'),

    path('process-risk-detector/', views.process_risk_detector_ia, name='process_risk_detector_ia'),
    path('process-iso-compliance-ia/', views.process_iso_compliance_ia, name='process_iso_compliance_ia'),
    path('process-summarize-ia/', views.process_summarize_ia, name='process_summarize_ia'),
    path('add-risk-processes/', views.add_risk_processes, name='add_risk_processes'),
]

