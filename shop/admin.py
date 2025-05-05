from django.contrib import admin
from .models import Product, Category, Customer, Seller, OrderStatusUpdate, OrderItem, Order

class Categoryinfo(admin.ModelAdmin):
    list_display = ["name"]

class ProductAdmin(admin.ModelAdmin):
    exclude = ('price',)  # Hide the price field in admin form
    list_display = ["name", "category", "price"]  # Show these columns in list view

    def save_model(self, request, obj, form, change):
        obj.save()  # Triggers the model's save method (price calculation)

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, Categoryinfo)
admin.site.register(Customer)
admin.site.register(Seller)
admin.site.register(OrderStatusUpdate)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.site_header = "Ecom Admin"
admin.site.site_title = "Ecom Admin Portal"
admin.site.index_title = "Welcome to Ecom Admin Portal"

 

