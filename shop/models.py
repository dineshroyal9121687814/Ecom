#shop/models.py
from django.db import models
from django.utils import timezone  
# Create your models here.
class Category(models.Model):
    name  = models.CharField(max_length=30)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=30)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=1)
    images = models.ImageField(upload_to='img')
    desc = models.TextField()
    price = models.FloatField()  # Will be auto-calculated
    original_price = models.FloatField()
    discount_percentage = models.FloatField()
    quantity = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    seller = models.ForeignKey('Seller', on_delete=models.CASCADE, related_name='products', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_new = models.BooleanField(default=False)  # Added as per previous discussion

    def __str__(self):
        return self.name
        
    def decrease_stock(self, quantity):
        try:
            current_stock = int(self.stock)
            if current_stock >= quantity:
                self.stock = current_stock - quantity
                self.save()
                return True
            return False
        except (ValueError, TypeError):
            print(f"Error: Product {self.id} has invalid stock value: {self.stock}")
            return False
    
    def save(self, *args, **kwargs):
        if not self.pk and self.stock == 0:
            self.stock = self.quantity
        if self.original_price and self.discount_percentage is not None:
            self.price = round(self.original_price * (1 - self.discount_percentage / 100), 2)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['discount_percentage']),
            models.Index(fields=['updated_at']),
        ]

class Customer(models.Model):
    first_name = models.CharField(max_length=30)
    last_name  = models.CharField(max_length=30)
    email      = models.EmailField(unique=True)
    mobile     = models.CharField(max_length=13,unique=True)
    password   = models.CharField(max_length=30)
    
    def isexist(self):
        if Customer.objects.filter(email=self.email).exists():
            return True
        elif Customer.objects.filter(mobile=self.mobile).exists():
            return True
        else:
            return False
        
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.FloatField()
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} ({self.discount_percentage}% off)"

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        """Calculate total price of all items in cart with coupon discount if applicable"""
        subtotal = sum(item.product.price * item.quantity for item in self.items.all())
        
        # Apply coupon discount if available
        if self.coupon and self.coupon.is_active:
            discount = subtotal * (self.coupon.discount_percentage / 100)
            return subtotal - discount
        
        return subtotal
    
    @property
    def item_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    

# models.py
class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"Payment {self.payment_id} for {self.customer.email}"
    

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('razorpay', 'Online Payment'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(max_length=500)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.email}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    

##################################### Seller details  ##################################################

class Seller(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=13, unique=True)
    password = models.CharField(max_length=100)
    business_name = models.CharField(max_length=100)
    business_address = models.TextField()
    gstin = models.CharField(max_length=15, null=True, blank=True)  # GST Identification Number
    approved = models.BooleanField(default=False)  # Admin approval status
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business_name} ({self.email})"
    
    def isexist(self):
        if Seller.objects.filter(email=self.email).exists():
            return True
        elif Seller.objects.filter(mobile=self.mobile).exists():
            return True
        else:
            return False


# Update Order model to track status changes
class OrderStatusUpdate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    updated_by_seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status}"
    




# In models.py - add these models

# class Order(models.Model):
#     ORDER_STATUS_CHOICES = (
#         ('pending', 'Pending'),
#         ('processing', 'Processing'),
#         ('shipped', 'Shipped'),
#         ('delivered', 'Delivered'),
#         ('cancelled', 'Cancelled'),
#     )
    
#     customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
#     payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
#     order_date = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     shipping_address = models.TextField()
#     city = models.CharField(max_length=100)
#     state = models.CharField(max_length=100)
#     pincode = models.CharField(max_length=20)
    
#     def __str__(self):
#         return f"Order #{self.id} - {self.customer.email}"