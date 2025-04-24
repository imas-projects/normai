from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
   
    #path('com-table',views.communication_table_view,name='communication_table_view'),
'''
    path('all-messages', views.all_messages, name='all_messages'),
    path('received-messages', views.user_received_messages, name='received_messages'),
    path('sent-messages', views.user_sent_messages, name='sent_messages'),
    path('communication-table-review', views.communication_table_review, name='communication_table_review'),
    path('create-table/', views.create_table, name='create-table'),

    path('load-form-options/', views.load_form_options, name='load_form_options'),
    path('load-messageform-options-asJson/', views.load_messageform_options_asJson, name='load_messageform_options_asJson'),
    path('load-addtableform-options-asJson/', views.load_addtableform_options_asJson, name='load_addtableform_options_asJson'),

    path('get-message/<int:id>/', views.get_message, name='get_message'),
    path('update-message/', views.update_message, name='update_message'),
    path('delete-message/<int:id>/', views.delete_message, name='delete-message'),
    path('create-message/', views.create_message, name='create-message'),
'''

  ]


