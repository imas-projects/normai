from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
   
    #path('com-table',views.communication_table_view,name='communication_table_view'),

    path('communication-tables', views.all_messages, name='communication_tables'),
    path('my-messages', views.user_received_sent_messages, name='received_sent_messages'),
    path('communication-table-review', views.communication_table_review, name='communication_table_review'),
    path('create-table/', views.create_table, name='create-table'),

    path('load-form-options/', views.load_form_options, name='load_form_options'),
    path('load-messageform-options-asJson/', views.load_messageform_options_asJson, name='load_messageform_options_asJson'),
    path('load-addtableform-options-asJson/', views.load_addtableform_options_asJson, name='load_addtableform_options_asJson'),

    path('get-message/<int:id>/', views.get_message, name='get_message'),
    path('update-message/', views.update_message, name='update_message'),
    path('delete-message/<int:id>/', views.delete_message, name='delete-message'),
    path('create-message/', views.create_message, name='create-message'),

    path('summarize-table/', views.table_summarize_ia, name='table-summarize-ia'),
    path('save-summarize-table/', views.save_table_summarize_ia, name='save_table_summarize_ia'),

    path('flow-map/', views.table_flow_map_ia, name='table_flow_map_ia'),

]
