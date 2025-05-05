# from django.db import models

# # Create your models here.
# class Seller(models.Model):
#     first_name = models.CharField(max_length=30)
#     last_name  = models.CharField(max_length=30)
#     email      = models.EmailField(unique=True)
#     mobile     = models.CharField(max_length=13,unique=True)
#     password   = models.CharField(max_length=30)
#     gst_number = models.CharField(max_length=15,unique=True)

#     def isexist(self):
#         if Seller.objects.filter(email=self.email).exists():
#             return True
#         elif Seller.objects.filter(mobile=self.mobile).exists():
#             return True
#         else:
#             return False

