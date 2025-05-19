from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from .models import Skill, Experience, Project, Education, Certification, Profile
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm

def home(request):
    """View for homepage"""
    profile = Profile.objects.first()
    skills = {
        'programming': Skill.objects.filter(category='programming'),
        'devops': Skill.objects.filter(category='devops'),
        'testing': Skill.objects.filter(category='testing'),
        'other': Skill.objects.filter(category='other'),
    }
    experiences = Experience.objects.all().prefetch_related('achievements')
    projects = Project.objects.all().prefetch_related('technologies')
    education = Education.objects.all()
    certifications = Certification.objects.all()
    
    context = {
        'profile': profile,
        'skills': skills,
        'experiences': experiences,
        'projects': projects,
        'education': education,
        'certifications': certifications,
    }
    
    return render(request, 'portfolio/home.html', context)

def contact_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Format the email content
            email_content = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            
            try:
                send_mail(
                    subject=subject,
                    message=email_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['DINESHROYAL9121@GMAIL.COM'],
                    fail_silently=False,
                )
                return render(request, 'portfolio/contact_form.html', {'message_sent': True})
            except Exception as e:
                # In a production environment, you might want to log the error
                return render(request, 'portfolio/contact_form.html', {'form': form, 'error': 'Failed to send email. Please try again.'})
    else:
        form = ContactForm()
    
    return render(request, 'portfolio/contact_form.html', {'form': form})


class AboutView(TemplateView):
    """View for about page"""
    template_name = 'portfolio/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.first()
        context['education'] = Education.objects.all()
        return context

class SkillsView(TemplateView):
    """View for skills page"""
    template_name = 'portfolio/skills.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.first()
        context['skills'] = {
            'programming': Skill.objects.filter(category='programming'),
            'devops': Skill.objects.filter(category='devops'),
            'testing': Skill.objects.filter(category='testing'),
            'other': Skill.objects.filter(category='other'),
        }
        return context

class ExperienceListView(ListView):
    """View for experience page"""
    model = Experience
    template_name = 'portfolio/experience.html'
    context_object_name = 'experiences'
    
    def get_queryset(self):
        return Experience.objects.all().prefetch_related('achievements')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.first()
        return context

class ProjectListView(ListView):
    """View for projects page"""
    model = Project
    template_name = 'portfolio/projects.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return Project.objects.all().prefetch_related('technologies')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.first()
        return context

class ContactView(TemplateView):
    """View for contact page"""
    template_name = 'portfolio/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = Profile.objects.first()
        return context