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
    path('load-responsible/', views.load_responsible, name='load_responsible'),

    path('process-risk-detector/', views.process_risk_detector_ia, name='process_risk_detector_ia'),
    path('process-iso-compliance-ia/', views.process_iso_compliance_ia, name='process_iso_compliance_ia'),
    path('process-summarize-ia/', views.process_summarize_ia, name='process_summarize_ia'),
    path('add-risk-processes/', views.add_risk_processes, name='add_risk_processes'),
    path('kpis-detector-ia/', views.kpis_detector_ia, name='kpis_detector_ia'),
    path('checklist-process/', views.checklist_detector_ia, name='checklist_detector_ia'),
    

    path('save-summary-processes/', views.save_process_summarize_ia, name='save_process_summarize_ia'),
    path('kpis/', views.kpis_processes, name='kpis_processes'),
    path('save-kpis/', views.save_kpi_processes, name='save_kpi_processes')
    
]



