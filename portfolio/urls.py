from django.urls import path
from . import views


app_name = 'portfolio'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('skills/', views.SkillsView.as_view(), name='skills'),
    path('experience/', views.ExperienceListView.as_view(), name='experience'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/send/', views.contact_form, name='send_contact_email'),
]