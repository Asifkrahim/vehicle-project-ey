from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add/', views.add_maintenance, name='add_maintenance'),
    path('delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('logout/', views.logout_view, name='logout'),
    path('chatbot-response/',views.chatbot_response,name='chatbot_response'),
]
