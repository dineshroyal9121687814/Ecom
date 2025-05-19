from django.contrib import admin
from .models import Skill, Experience, Achievement, Project, Education, Certification, Profile


admin.site.register(Skill)
admin.site.register(Experience)
admin.site.register(Achievement)
admin.site.register(Project)
admin.site.register(Education)
admin.site.register(Certification)
admin.site.register(Profile)
admin.site.site_header = "Portfolio Admin"
admin.site.site_title = "Portfolio Admin Portal"
admin.site.index_title = "Welcome to Portfolio Admin Portal"