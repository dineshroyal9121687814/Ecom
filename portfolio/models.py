from django.db import models

class Skill(models.Model):
    """Model for technical skills"""
    CATEGORY_CHOICES = [
        ('programming', 'Programming Languages'),
        ('devops', 'DevOps & Cloud'),
        ('testing', 'Testing & Automation'),
        ('other', 'Other Tools'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    def __str__(self):
        return self.name

class Experience(models.Model):
    """Model for work experience"""
    company = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.position} at {self.company}"

class Achievement(models.Model):
    """Model for work achievements"""
    experience = models.ForeignKey(Experience, related_name='achievements', on_delete=models.CASCADE)
    description = models.TextField()
    
    def __str__(self):
        return self.description[:50]

class Project(models.Model):
    """Model for portfolio projects"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='portfolio/projects/', null=True, blank=True)
    github_url = models.URLField(blank=True, null=True)
    live_url = models.URLField(blank=True, null=True)
    technologies = models.ManyToManyField(Skill, related_name='projects')
    
    def __str__(self):
        return self.title

class Education(models.Model):
    """Model for education background"""
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    score = models.CharField(max_length=50, blank=True)
    year = models.IntegerField()
    
    def __str__(self):
        return f"{self.degree} - {self.institution}"


class Certification(models.Model):
    """Model for certifications"""
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, blank=True)
    date_obtained = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    """Model for personal profile information"""
    name = models.CharField(max_length=100, default="VC DINESH")
    title = models.CharField(max_length=200, default="Software Engineer")
    location = models.CharField(max_length=100, default="Bengaluru - 560103")
    phone = models.CharField(max_length=20, default="9121687814")
    email = models.EmailField(default="DINESHROYAL9121@GMAIL.COM")
    linkedin = models.URLField(default="https://www.linkedin.com/in/dinesh-royal-4a66441b8/")
    github = models.URLField(default="https://github.com/dineshroyal9121687814")
    summary = models.TextField(default="Software engineer with 2+ years of experience. Executed automatic setups locally for testing and created Jenkins pipelines. Experienced in automation and UI development, with hands-on expertise in AWS, Docker, and Kubernetes, while actively expanding knowledge in DevOps practices.")
    
    def __str__(self):
        return self.name