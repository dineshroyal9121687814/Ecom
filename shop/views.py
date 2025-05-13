from datetime import timedelta, timezone
import json
import os

from django.contrib import messages
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Sum
from django.core.paginator import Paginator

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework.response import Response

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.template.loader import render_to_string
import logging
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.core.cache import cache
from django.template.loader import render_to_string



import razorpay
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Cart, Customer, Payment
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt




razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

def place_order(request):
    if request.method == 'POST':
        customer_id = request.session.get('customer_id')
        if not customer_id:
            return redirect('login')
        
        customer = Customer.objects.get(id=customer_id)
        cart = Cart.objects.get(customer=customer)
        
        available_item_ids = request.session.get('available_item_ids', [])
        if not available_item_ids:
            available_items = [item for item in cart.items.all() if item.product.stock > 0]
            available_item_ids = [item.id for item in available_items]
        
        available_cart_items = cart.items.filter(id__in=available_item_ids)
        
        subtotal = sum(item.product.price * item.quantity for item in available_cart_items)
        total_amount = subtotal * 1.18  # Including 18% tax
        total_amount_paise = int(total_amount * 100)  # Convert to paise for Razorpay
        
        # Get shipping details from POST data
        shipping_address = request.POST.get('address', '')  
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        pincode = request.POST.get('pincode', '')
        
        # Validate shipping details regardless of payment method
        if not all([shipping_address, city, state, pincode]):
            messages.error(request, "Incomplete shipping details. Please provide all address fields.")
            return redirect('checkout')
        
        # Store shipping details in session for Razorpay payment flow
        request.session['shipping_address'] = shipping_address
        request.session['shipping_city'] = city
        request.session['shipping_state'] = state
        request.session['shipping_pincode'] = pincode
        
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'cod':
            # Handle COD: Create order directly            
            order = Order.objects.create(
                customer=customer,
                payment=None,  # No payment for COD
                total_amount=total_amount,
                shipping_address=shipping_address,
                city=city,
                state=state,
                pincode=pincode,
                payment_method='cod',
                status='pending'
            )
            
            for item in available_cart_items:
                if item.product.stock > 0:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=min(item.quantity, item.product.stock),
                        price=item.product.price
                    )
                    try:
                        item.product.decrease_stock(item.quantity)
                    except (ValueError, TypeError) as e:
                        print(f"Error decreasing stock for product {item.product.id}: {str(e)}")
                item.delete()
            
            request.session['last_order_id'] = order.id
            # Clean up session data
            keys_to_clean = ['available_item_ids', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_pincode']
            for key in keys_to_clean:
                if key in request.session:
                    del request.session[key]
                    
            return redirect('order_success')  # Changed to order_success for COD
        
        # Razorpay payment
        razorpay_order = razorpay_client.order.create({
            'amount': total_amount_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        request.session['razorpay_order_id'] = razorpay_order['id']
        request.session['available_cart_items'] = list(available_cart_items.values_list('id', flat=True))
        
        return render(request, 'payment.html', {
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'amount': total_amount_paise,
            'customer': customer,
            'cart': cart,
            'available_items': available_cart_items,
            'subtotal': subtotal,
            'tax_amount': subtotal * 0.18,
            'total': total_amount
        })
    
    return redirect('checkout')
    

@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data.get('payment_id')
            order_id = data.get('order_id')
            signature = data.get('signature')
            
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            customer_id = request.session.get('customer_id')
            if not customer_id:
                return JsonResponse({'status': 'error', 'message': 'Customer not found'})
            
            customer = Customer.objects.get(id=customer_id)
            cart = Cart.objects.get(customer=customer)
            
            available_item_ids = request.session.get('available_cart_items', [])
            available_cart_items = cart.items.filter(id__in=available_item_ids)
            
            available_total = sum(item.product.price * item.quantity for item in available_cart_items)
            final_amount = available_total * 1.18
            
            payment = Payment.objects.create(
                customer=customer,
                order_id=order_id,
                payment_id=payment_id,
                amount=final_amount,
                status="success"
            )
            
            # Get shipping details from session
            shipping_address = request.session.get('shipping_address', '')
            city = request.session.get('shipping_city', '')
            state = request.session.get('shipping_state', '')
            pincode = request.session.get('shipping_pincode', '')
            
            # Validate shipping details
            if not all([shipping_address, city, state, pincode]):
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Incomplete shipping details. Please provide all address fields.',
                    'redirect': '/checkout/'
                })
            
            order = Order.objects.create(
                customer=customer,
                payment=payment,
                total_amount=final_amount,
                shipping_address=shipping_address,
                city=city,
                state=state,
                pincode=pincode,
                payment_method='razorpay',
                status='processing'
            )
            
            for item in available_cart_items:
                if item.product.stock > 0:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=min(item.quantity, item.product.stock),
                        price=item.product.price
                    )
                    try:
                        item.product.decrease_stock(item.quantity)
                    except (ValueError, TypeError) as e:
                        print(f"Error decreasing stock for product {item.product.id}: {str(e)}")
                
                item.delete()
            
            request.session['last_order_id'] = order.id
            
            # Clean up all session data
            keys_to_clean = [
                'available_cart_items',
                'available_item_ids',
                'razorpay_order_id',
                'shipping_address',
                'shipping_city',
                'shipping_state',
                'shipping_pincode'
            ]
            for key in keys_to_clean:
                if key in request.session:
                    del request.session[key]
            
            return JsonResponse({'status': 'success'})
            
        except razorpay.errors.SignatureVerificationError as e:
            return JsonResponse({'status': 'error', 'message': 'Invalid payment signature'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def payment_success(request):
    order_id = request.session.get('last_order_id')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            return render(request, 'payment_success.html', {
                'order': order,
                'order_items': order.items.all()
            })
        except Order.DoesNotExist:
            pass
    
    # If no order found or error, show generic success page
    return render(request, 'payment_success.html')


def order_success(request):
    order_id = request.session.get('last_order_id')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            return render(request, 'order_success.html', {
                'order': order,
                'order_items': order.items.all()
            })
        except Order.DoesNotExist:
            pass
    
    # If no order found or error, show generic success page
    return render(request, 'order_success.html')

def order_history(request):
    """Show customer's order history"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(id=customer_id)
        orders = Order.objects.filter(customer=customer).order_by('-order_date')
    except Customer.DoesNotExist:
        orders = []
    
    return render(request, 'order_history.html', {'orders': orders})

def order_detail(request, order_id):
    """Show details of a specific order"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(id=customer_id)
        order = Order.objects.get(id=order_id, customer=customer)
        order_items = order.items.all()
    except (Customer.DoesNotExist, Order.DoesNotExist):
        messages.error(request, "Order not found.")
        return redirect('order_history')
    
    return render(request, 'order_detail.html', {
        'order': order,
        'order_items': order_items
    })

def get_products(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'Products': products})

def cart_view(request):
    """Show the cart contents"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    try:
        customer = Customer.objects.get(id=customer_id)
        cart, created = Cart.objects.get_or_create(customer=customer)
        cart_items = cart.items.all()
        
        # Check if any items are out of stock
        has_unavailable_items = any(item.product.stock <= 0 for item in cart_items)
        
    except Exception as e:
        cart_items = []
        cart = None
        has_unavailable_items = False
    
    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'has_unavailable_items': has_unavailable_items
    })

@api_view(['POST'])
def add_to_cart_api(request):
    data = request.data
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    buy_now = data.get('buy_now', False)
    clear_cart = data.get('clear_cart', False)
    
    # Check if user is logged in
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({
            'error': 'Please login to add items to cart',
            'status': 'authentication_required'
        }, status=401)
    
    try:
        product = Product.objects.get(id=product_id)
        customer = Customer.objects.get(id=customer_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=404)

    # Get or create cart for this customer
    cart, created = Cart.objects.get_or_create(customer=customer)
    
    # If buy_now with clear_cart, clear the cart first
    if buy_now and clear_cart:
        cart.items.all().delete()
        
        # Store the buy_now flag and product ID in session
        request.session['buy_now'] = True
        request.session['buy_now_product_id'] = product_id
    
    # Check if product already in cart
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += quantity
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)

    return Response({
        'message': 'Item added to cart',
        'cart_count': cart.item_count
    })

@api_view(['POST'])
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(id=item_id)
            product = cart_item.product
            
            # Check if requested quantity is available in stock
            if quantity > product.stock:
                # Return an error response if quantity exceeds stock
                return JsonResponse({
                    'status': 'error',
                    'message': f'Only {product.stock} items available in stock',
                    'available_stock': product.stock,
                    'cart_total': cart_item.cart.total_price,
                    'cart_count': cart_item.cart.item_count
                })
            
            # If quantity is 0, remove the item
            if quantity <= 0:
                cart_item.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Item removed from cart',
                    'cart_total': cart_item.cart.total_price,
                    'cart_count': cart_item.cart.item_count
                })
            
            # Update the quantity
            cart_item.quantity = quantity
            cart_item.save()
            
            # Refresh the cart to get updated totals
            cart = Cart.objects.get(id=cart_item.cart.id)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Cart updated successfully',
                'cart_total': cart.total_price,
                'cart_count': cart.item_count
            })
            
        except CartItem.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Cart item not found'
            }, status=404)
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@api_view(['POST'])
def remove_from_cart(request):
    """Remove item from cart"""
    data = request.data
    item_id = data.get('item_id')
    
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Please login to update cart'}, status=401)
    
    try:
        cart_item = CartItem.objects.get(id=item_id)
        # Verify item belongs to this customer
        if cart_item.cart.customer.id != customer_id:
            return Response({'error': 'Unauthorized'}, status=403)
        
        cart = cart_item.cart
        cart_item.delete()
        
        return Response({
            'message': 'Item removed from cart',
            'cart_count': cart.item_count,
            'cart_total': cart.total_price
        })
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=404)
    
@api_view(['POST'])
def clear_cart(request):
    """Remove all items from cart"""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Please login to clear cart'}, status=401)
    
    try:
        customer = Customer.objects.get(id=customer_id)
        cart = Cart.objects.get(customer=customer)
        # Delete all cart items
        cart.items.all().delete()
        
        return Response({
            'message': 'Cart cleared successfully',
            'cart_count': 0,
            'cart_total': 0.00
        })
    except (Customer.DoesNotExist, Cart.DoesNotExist):
        return Response({'error': 'Cart not found'}, status=404)

@api_view(['POST'])
def get_cart_item_id(request):
    data = request.data
    product_id = data.get('product_id')
    
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'status': 'error', 'message': 'Please login to perform this action'}, status=401)
    
    try:
        customer = Customer.objects.get(id=customer_id)
        cart = Cart.objects.get(customer=customer)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        
        return Response({
            'status': 'success',
            'item_id': cart_item.id
        })
    except (Customer.DoesNotExist, Cart.DoesNotExist, CartItem.DoesNotExist):
        return Response({'status': 'error', 'message': 'Item not found in cart'}, status=404)


def apply_coupon(request):
    """Apply a coupon code to the cart"""
    if request.method == 'POST':
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')
        
        customer_id = request.session.get('customer_id')
        if not customer_id:
            return JsonResponse({'status': 'error', 'message': 'Please login to apply coupon'}, status=401)
        
        try:
            customer = Customer.objects.get(id=customer_id)
            cart = Cart.objects.get(customer=customer)
            
            # Check if coupon code exists and is valid
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                # Check if coupon is expired
                if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                    return JsonResponse({'status': 'error', 'message': 'Coupon has expired'}, status=400)
                    
                # Apply coupon to cart
                cart.coupon = coupon
                cart.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Coupon applied successfully',
                    'discount': coupon.discount_percentage,
                    'cart_total': cart.total_price
                })
            except Coupon.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid coupon code'}, status=400)
                
        except (Customer.DoesNotExist, Cart.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Cart not found'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)




def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', '')

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    if category_id:
        try:
            # Convert to integer to avoid type errors
            category_id = int(category_id)
            products = products.filter(category_id=category_id)
        except (ValueError, TypeError):
            # Handle invalid category_id gracefully
            pass

    # Apply sorting
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'high_discount':
        products = products.order_by('-discount_percentage')

    # Paginate the filtered products
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Filter New Arrivals
    recent_threshold = timezone.now() - timedelta(days=7)
    new_products = Product.objects.filter(
        models.Q(discount_percentage__gte=15) |
        models.Q(updated_at__gte=recent_threshold)
    ).order_by('-discount_percentage', '-updated_at')[:15]
    
    # Group products into sets of 3 for the carousel
    grouped_new_products = [new_products[i:i+3] for i in range(0, len(new_products), 3)]

    categories = Category.objects.all()
    
    # Get cart if user is logged in
    cart = None
    if request.session.get('customer_id'):
        try:
            customer = Customer.objects.get(id=request.session.get('customer_id'))
            cart, created = Cart.objects.get_or_create(customer=customer)
        except Customer.DoesNotExist:
            pass

    return render(request, 'index.html', {
        'Products': page_obj,
        'NewProducts': new_products,
        'GroupedNewProducts': grouped_new_products,
        'Categories': categories,
        'query': query,
        'category': category_id,
        'sort': sort,
        'cart': cart,  # Make sure cart is included in context
    })




logger = logging.getLogger(__name__)

def products_partial(request):
    """
    View to return partial HTML for products based on filters.
    Returns JSON with rendered HTML for AJAX requests.
    """
    try:
        # Get query parameters
        category_id = request.GET.get('category', '')
        query = request.GET.get('q', '').strip()
        sort = request.GET.get('sort', '')
        page = request.GET.get('page', '1')

        # Start with all products
        products = Product.objects.all()

        # Apply filters
        if category_id:
            try:
                category_id = int(category_id)
                products = products.filter(category_id=category_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid category_id: {category_id}")
                # Continue without filtering by category

        if query:
            products = products.filter(Q(name__icontains=query) | Q(desc__icontains=query))

        # Apply sorting
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'newest':
            products = products.order_by('-created_at')
        elif sort == 'high_discount':
            products = products.order_by('-discount_percentage')

        # Paginate results
        paginator = Paginator(products, 12)  # Show 12 products per page
        try:
            product_page = paginator.page(page)
        except PageNotAnInteger:
            product_page = paginator.page(1)
        except EmptyPage:
            product_page = paginator.page(paginator.num_pages)

        # Get cart if user is logged in
        cart = None
        customer_id = request.session.get('customer_id')
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                cart, created = Cart.objects.get_or_create(customer=customer)
            except Customer.DoesNotExist:
                logger.warning(f"Customer not found for ID: {customer_id}")

        # Render partial template
        html = render_to_string('products_partial.html', {
            'Products': product_page,
            'query': query,
            'cart': cart,
            'category': category_id,
            'sort': sort,
        }, request=request)

        # Return JSON response
        return JsonResponse({
            'html': html,
            'page': int(page),
            'has_next': product_page.has_next(),
            'has_previous': product_page.has_previous(),
            'total_pages': paginator.num_pages,
        })

    except Exception as e:
        logger.error(f"Error in products_partial view: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Failed to load products: {str(e)}'
        }, status=500)


# Add a product detail view - this was likely missing
def product_detail(request, product_id):
    """View details of a specific product"""
    try:
        product = Product.objects.get(id=product_id)
        # Get related products from same category
        related_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id).order_by('?')[:4]  # Get 4 random related products
        
        # Check if product is in cart
        in_cart = False
        cart = None
        if request.session.get('customer_id'):
            try:
                customer = Customer.objects.get(id=request.session.get('customer_id'))
                cart, created = Cart.objects.get_or_create(customer=customer)
                in_cart = cart.items.filter(product=product).exists()
            except Customer.DoesNotExist:
                pass
        
        return render(request, 'product_detail.html', {
            'product': product,
            'related_products': related_products,
            'in_cart': in_cart,
            'cart': cart
        })
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('product_list')


def new_arrivals(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # Cache NewProducts for 10 minutes
    cache_key = 'new_products'
    new_products = cache.get(cache_key)
    if not new_products:
        recent_threshold = timezone.now() - timedelta(days=7)
        new_products = Product.objects.filter(
            models.Q(discount_percentage__gte=15) |
            models.Q(updated_at__gte=recent_threshold)
        ).only('id', 'name', 'images', 'price', 'original_price', 'discount_percentage', 'stock', 'is_new')\
         .order_by('-discount_percentage', '-updated_at')[:15]
        cache.set(cache_key, new_products, 600)

    # Group products into sets of 3
    grouped_new_products = [new_products[i:i+3] for i in range(0, len(new_products), 3)]

    # Get cart for button states
    cart = None
    if request.session.get('customer_id'):
        try:
            customer = Customer.objects.get(id=request.session.get('customer_id'))
            cart, created = Cart.objects.get_or_create(customer=customer)
        except Customer.DoesNotExist:
            pass

    # Render partial template
    html = render_to_string('new_arrivals_partial.html', {
        'GroupedNewProducts': grouped_new_products,
        'cart': cart
    })

    return JsonResponse({'html': html})

@api_view(['POST'])
def check_cart_status(request):
    data = request.data
    product_ids = data.get('product_ids', [])
    
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({
            'status': 'error', 
            'message': 'User not logged in',
            'in_cart_products': []
        })
    
    try:
        customer = Customer.objects.get(id=customer_id)
        cart = Cart.objects.get(customer=customer)
        
        # Get all products from cart that match the provided IDs
        in_cart_items = CartItem.objects.filter(cart=cart, product_id__in=product_ids)
        in_cart_product_ids = [str(item.product_id) for item in in_cart_items]
        
        return Response({
            'status': 'success',
            'in_cart_products': in_cart_product_ids
        })
    except (Customer.DoesNotExist, Cart.DoesNotExist):
        return Response({
            'status': 'error',
            'message': 'Cart not found',
            'in_cart_products': []
        })


def checkout(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')
    
    # Check for buy_now parameter
    buy_now_product_id = request.GET.get('buy_now')
    is_buy_now = buy_now_product_id is not None or request.session.get('buy_now', False)
    
    try:
        customer = Customer.objects.get(id=customer_id)
        cart = Cart.objects.get(customer=customer)
        
        # Handle buy_now case
        if is_buy_now:
            # Reset the session flag
            if 'buy_now' in request.session:
                del request.session['buy_now']
                
            # Get the product ID from session if not in URL
            if not buy_now_product_id and 'buy_now_product_id' in request.session:
                buy_now_product_id = request.session['buy_now_product_id']
                del request.session['buy_now_product_id']
            
            # Only include the specified product
            if buy_now_product_id:
                available_items = cart.items.filter(product_id=buy_now_product_id, product__stock__gt=0)
                # Store the buy_now info in session for place_order
                request.session['is_buy_now'] = True
                request.session['buy_now_product_id'] = buy_now_product_id
            else:
                # Fallback to all available items if no specific product is found
                available_items = [item for item in cart.items.all() if item.product.stock > 0]
        else:
            # Regular checkout with all available items
            available_items = [item for item in cart.items.all() if item.product.stock > 0]
            # Clear any buy_now flags
            if 'is_buy_now' in request.session:
                del request.session['is_buy_now']
            if 'buy_now_product_id' in request.session:
                del request.session['buy_now_product_id']
        
        if not available_items:
            messages.warning(request, "Your cart doesn't contain any available items. Please add items in stock before checkout.")
            return redirect('cart')
            
        available_total = sum(item.product.price * item.quantity for item in available_items)
        
        # Store available item IDs in session
        if isinstance(available_items, list):
            available_item_ids = [item.id for item in available_items]
        else:
            available_item_ids = list(available_items.values_list('id', flat=True))
        
        # Store these IDs in session for access in place_order
        request.session['available_item_ids'] = available_item_ids
        # Also store as available_cart_items for compatibility with verify_payment function
        request.session['available_cart_items'] = available_item_ids
        
    except Exception as e:
        messages.error(request, f"There was an error with your cart: {str(e)}")
        return redirect('cart')
    
    if request.method == 'POST':
        # Process checkout form submission
        shipping_address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        
        # Validate inputs
        if not all([shipping_address, city, state, pincode]):
            messages.error(request, "Please fill in all address fields.")
            return render(request, 'checkout.html', {
                'cart': cart,
                'customer': customer,
                'available_items': available_items,
                'available_total': available_total,
                'is_buy_now': is_buy_now,
            })
        
        # Store shipping details in session
        request.session['shipping_address'] = shipping_address
        request.session['shipping_city'] = city
        request.session['shipping_state'] = state
        request.session['shipping_pincode'] = pincode
        
        # Make sure we preserve the available_item_ids when redirecting
        return redirect('place_order')
    
    # Render checkout page
    return render(request, 'checkout.html', {
        'cart': cart,
        'customer': customer,
        'available_items': available_items,
        'available_total': available_total,
        'is_buy_now': is_buy_now,
    })


def login(request):
    if request.method == 'GET':
        # Check for action and product_id to save in session for after login
        action = request.GET.get('action')
        product_id = request.GET.get('product_id')
        
        if action and product_id:
            # Store in session to handle after successful login
            request.session['after_login_action'] = action
            request.session['after_login_product_id'] = product_id
            
        return render(request, 'login.html')
    else:
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            customer = Customer.objects.get(email=email)
            if check_password(password, customer.password):
                # Store session data
                request.session['customer_id'] = customer.id
                request.session['customer_name'] = customer.first_name
                
                # Check if there's a pending action from before login
                after_login_action = request.session.pop('after_login_action', None)
                product_id = request.session.pop('after_login_product_id', None)
                
                if after_login_action and product_id:
                    if after_login_action == 'cart':
                        # Rather than encoding in the URL, add an item to cart then redirect
                        try:
                            product = Product.objects.get(id=product_id)
                            cart, created = Cart.objects.get_or_create(customer=customer)
                            
                            # Check if product already in cart
                            try:
                                cart_item = CartItem.objects.get(cart=cart, product=product)
                                cart_item.quantity += 1
                                cart_item.save()
                            except CartItem.DoesNotExist:
                                CartItem.objects.create(cart=cart, product=product, quantity=1)
                                
                            # Set a message to show after redirect
                            messages.success(request, "Product added to your cart!")
                        except Product.DoesNotExist:
                            messages.error(request, "Product not found")
                        
                        # Redirect to product list page
                        return redirect('product_list')
                    
                    elif after_login_action == 'buy':
                        # For buy now, we set up session then redirect to checkout
                        try:
                            product = Product.objects.get(id=product_id)
                            cart, created = Cart.objects.get_or_create(customer=customer)
                            cart.items.all().delete()  # Clear cart for buy now
                            CartItem.objects.create(cart=cart, product=product, quantity=1)
                            
                            # Set buy now flags in session
                            request.session['buy_now'] = True
                            request.session['buy_now_product_id'] = product_id
                            
                            return redirect('checkout')
                        except Product.DoesNotExist:
                            messages.error(request, "Product not found")
                            return redirect('product_list')
                
                # Default redirect if no pending action
                return redirect('product_list')
            else:
                msg = "Invalid email or password"
        except Customer.DoesNotExist:
            msg = "User does not exist"

        return render(request, 'login.html', {'msg': msg, 'email': email})


def signup(request):
    if request.method == 'GET':
        # Check for action and product_id to save in session for after signup
        action = request.GET.get('action')
        product_id = request.GET.get('product_id')
        
        if action and product_id:
            # Store in session to handle after successful signup
            request.session['after_signup_action'] = action
            request.session['after_signup_product_id'] = product_id
            
        return render(request, 'signup.html')
    else:
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        mobile = request.POST['mobile']
        password = make_password(request.POST['password'])

        userdata = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile': mobile
        }

        # Check if the user already exists
        if Customer.objects.filter(email=email).exists() or Customer.objects.filter(mobile=mobile).exists():
            msg = "User already exists with this email or mobile number"
            return render(request, 'signup.html', {'msg': msg, **userdata})
        else:
            # Save the new user
            customer = Customer(first_name=first_name, last_name=last_name, email=email, mobile=mobile, password=password)
            customer.save()
            # Automatically log in the user
            request.session['customer_id'] = customer.id
            request.session['customer_name'] = customer.first_name
            # Create a cart for the new user
            cart = Cart.objects.create(customer=customer)
            
            # Check if there's a pending action from before signup
            after_signup_action = request.session.pop('after_signup_action', None)
            product_id = request.session.pop('after_signup_product_id', None)
            
            if after_signup_action and product_id:
                try:
                    product = Product.objects.get(id=product_id)
                    
                    if after_signup_action == 'cart':
                        # Add to cart and redirect to product list
                        CartItem.objects.create(cart=cart, product=product, quantity=1)
                        messages.success(request, "Product added to your cart!")
                        return redirect('product_list')
                    
                    elif after_signup_action == 'buy':
                        # For buy now, add to cart and redirect to checkout
                        cart.items.all().delete()  # Clear cart for buy now
                        CartItem.objects.create(cart=cart, product=product, quantity=1)
                        
                        # Set buy now flags in session
                        request.session['buy_now'] = True
                        request.session['buy_now_product_id'] = product_id
                        
                        return redirect('checkout')
                
                except Product.DoesNotExist:
                    messages.error(request, "Product not found")
            
            # Default redirect if no pending action
            return redirect('product_list')
def logout(request):
    # Clear the session data
    if 'customer_id' in request.session:
        del request.session['customer_id']
    if 'customer_name' in request.session:
        del request.session['customer_name']
    if 'buy_now' in request.session:
        del request.session['buy_now']
    if 'buy_now_product_id' in request.session:
        del request.session['buy_now_product_id']
        
    # Redirect to home page
    return redirect('product_list')


def check_session(request):
    is_logged_in = 'customer_id' in request.session
    return JsonResponse({'logged_in': is_logged_in})


def profile(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login')

    customer = Customer.objects.get(id=customer_id)

    if request.method == "POST":
        customer.first_name = request.POST['first_name']
        customer.last_name = request.POST['last_name']
        customer.email = request.POST['email']
        customer.mobile = request.POST['mobile']
        new_password = request.POST.get('password')
        if new_password:
            customer.password = make_password(new_password)
        customer.save()
        msg = "Profile updated successfully"
        return render(request, 'profile.html', {'customer': customer, 'msg': msg})
    
    return render(request, 'profile.html', {'customer': customer})


################################## seller ##########################################
def seller_signup(request):
    if request.method == 'GET':
        return render(request, 'seller_signup.html')
    else:
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        mobile = request.POST['mobile']
        password = make_password(request.POST['password'])
        business_name = request.POST['business_name']
        business_address = request.POST['business_address']
        gstin = request.POST.get('gstin', '')

        seller_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile': mobile,
            'business_name': business_name,
            'business_address': business_address,
            'gstin': gstin
        }

        msg = None
        # Check if the seller already exists
        if Seller.objects.filter(email=email).exists() or Seller.objects.filter(mobile=mobile).exists():
            msg = "Seller already exists with this email or mobile number"
            return render(request, 'seller_signup.html', {'msg': msg, **seller_data})
        else:
            # Save the new seller
            seller = Seller(
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile=mobile,
                password=password,
                business_name=business_name,
                business_address=business_address,
                gstin=gstin
            )
            seller.save()
            creation_msg = "Registration successful! Your account is pending approval."
            return render(request, 'seller_signup.html', {'creation_msg': creation_msg})

def seller_login(request):
    if request.method == 'GET':
        return render(request, 'seller_login.html')
    else:
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            seller = Seller.objects.get(email=email)
            if check_password(password, seller.password):
                if not seller.approved:
                    msg = "Your account is pending approval. Please wait for admin confirmation."
                    return render(request, 'seller_login.html', {'msg': msg, 'email': email})
                    
                # Store session data
                request.session['seller_id'] = seller.id
                request.session['seller_name'] = seller.first_name
                request.session['business_name'] = seller.business_name
                return redirect('seller_dashboard')
            else:
                msg = "Invalid email or password"
        except Seller.DoesNotExist:
            msg = "Seller does not exist"

        return render(request, 'seller_login.html', {'msg': msg, 'email': email})

def seller_logout(request):
    # Clear seller session data
    if 'seller_id' in request.session:
        del request.session['seller_id']
    if 'seller_name' in request.session:
        del request.session['seller_name']
    if 'business_name' in request.session:
        del request.session['business_name']
    
    return redirect('seller_login')




def seller_dashboard(request):
    """Main dashboard for sellers showing key metrics"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        # Get all products by this seller
        products = Product.objects.filter(seller=seller)
        
        # Get recent orders containing seller's products
        seller_products_ids = products.values_list('id', flat=True)
        
        # Get order items for this seller's products
        order_items = OrderItem.objects.filter(product__id__in=seller_products_ids)
        
        # Get unique orders
        orders = Order.objects.filter(
            items__product__seller=seller
        ).distinct()
        
        # Calculate dashboard metrics
        total_products = products.count()
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        processing_orders = orders.filter(status='processing').count()
        shipped_orders = orders.filter(status='shipped').count()
        delivered_orders = orders.filter(status='delivered').count()
        
        # Calculate revenue
        revenue = order_items.aggregate(
            total_revenue=Sum('price')
        )['total_revenue'] or 0
        
        # Get products with low stock (less than 5)
        low_stock_products = products.filter(stock__lt=5)
        
        # Get recent orders (last 5)
        recent_orders = orders.order_by('-order_date')[:5]
        
        context = {
            'seller': seller,
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders': delivered_orders,
            'revenue': revenue,
            'low_stock_products': low_stock_products,
            'recent_orders': recent_orders
        }
        
        return render(request, 'seller_dashboard.html', context)
        
    except Seller.DoesNotExist:
        # If seller doesn't exist, clear session and redirect to login
        return redirect('seller_logout')

def seller_products(request):
    """View all products of a seller"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        products = Product.objects.filter(seller=seller).order_by('-id')
        
        # Add pagination
        paginator = Paginator(products, 10)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        categories = Category.objects.all()
        
        return render(request, 'seller_products.html', {
            'seller': seller,
            'page_obj': page_obj,
            'categories': categories
        })
        
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def add_product(request):
    """Add a new product"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        if request.method == 'POST':
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            desc = request.POST.get('desc')
            original_price = float(request.POST.get('original_price'))
            discount_percentage = float(request.POST.get('discount_percentage', 0))
            quantity = int(request.POST.get('quantity', 0))
            
            # Get category
            category = Category.objects.get(id=category_id)
            
            # Handle image upload
            image = request.FILES.get('image')
            
            # Create product
            product = Product(
                name=name,
                category=category,
                desc=desc,
                original_price=original_price,
                discount_percentage=discount_percentage,
                quantity=quantity,
                stock=quantity,
                seller=seller
            )
            
            if image:
                product.images = image
                
            product.save()
            
            messages.success(request, "Product added successfully!")
            return redirect('seller_products')
        
        categories = Category.objects.all()
        return render(request, 'add_product.html', {
            'seller': seller,
            'categories': categories
        })
        
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def edit_product(request, product_id):
    """Edit an existing product"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        product = Product.objects.get(id=product_id, seller=seller)
        
        if request.method == 'POST':
            product.name = request.POST.get('name')
            product.category_id = request.POST.get('category')
            product.desc = request.POST.get('desc')
            product.original_price = float(request.POST.get('original_price'))
            product.discount_percentage = float(request.POST.get('discount_percentage', 0))
            
            # Handle new quantity/stock
            new_quantity = int(request.POST.get('quantity', 0))
            if new_quantity > product.quantity:
                # Add the difference to stock
                product.stock += (new_quantity - product.quantity)
            product.quantity = new_quantity
            
            # Handle image upload
            if 'image' in request.FILES:
                product.images = request.FILES['image']
                
            product.save()
            
            messages.success(request, "Product updated successfully!")
            return redirect('seller_products')
        
        categories = Category.objects.all()
        return render(request, 'edit_product.html', {
            'seller': seller,
            'product': product,
            'categories': categories
        })
        
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('seller_products')
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def seller_orders(request):
    """View all orders containing seller's products"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        # Filter orders by status if provided
        status_filter = request.GET.get('status', '')
        
        # Get all orders containing seller's products
        orders = Order.objects.filter(
            items__product__seller=seller
        ).distinct().order_by('-order_date')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        # Add pagination
        paginator = Paginator(orders, 10)  # Show 10 orders per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'seller_orders.html', {
            'seller': seller,
            'page_obj': page_obj,
            'status_filter': status_filter,
            'order_status_choices': Order.ORDER_STATUS_CHOICES
        })
        
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def seller_order_detail(request, order_id):
    """View details of a specific order"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        # Get the order
        order = Order.objects.get(id=order_id)
        
        # Check if this order contains seller's products
        seller_items = order.items.filter(product__seller=seller)
        
        if not seller_items.exists():
            messages.error(request, "You don't have permission to view this order")
            return redirect('seller_orders')
        
        # Get order status updates
        status_updates = order.status_updates.all().order_by('-timestamp')
        
        return render(request, 'seller_order_detail.html', {
            'seller': seller,
            'order': order,
            'seller_items': seller_items,
            'status_updates': status_updates,
            'order_status_choices': Order.ORDER_STATUS_CHOICES
        })
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('seller_orders')
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def update_order_status(request, order_id):
    """Update the status of an order"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    if request.method != 'POST':
        return redirect('seller_order_detail', order_id=order_id)
    
    new_status = request.POST.get('status')
    comment = request.POST.get('comment', '')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        order = Order.objects.get(id=order_id)
        
        # Check if this order contains seller's products
        seller_items = order.items.filter(product__seller=seller)
        
        if not seller_items.exists():
            messages.error(request, "You don't have permission to update this order")
            return redirect('seller_orders')
        
        # Update order status
        order.status = new_status
        order.save()
        
        # Create status update record
        OrderStatusUpdate.objects.create(
            order=order,
            status=new_status,
            comment=comment,
            updated_by_seller=seller
        )
        
        messages.success(request, f"Order status updated to {new_status}")
        return redirect('seller_order_detail', order_id=order_id)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('seller_orders')
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def seller_profile(request):
    """View and edit seller profile"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        if request.method == 'POST':
            seller.first_name = request.POST.get('first_name')
            seller.last_name = request.POST.get('last_name')
            seller.email = request.POST.get('email')
            seller.mobile = request.POST.get('mobile')
            seller.business_name = request.POST.get('business_name')
            seller.business_address = request.POST.get('business_address')
            seller.gstin = request.POST.get('gstin')
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                seller.password = make_password(new_password)
                
            seller.save()
            
            # Update session data
            request.session['seller_name'] = seller.first_name
            request.session['business_name'] = seller.business_name
            
            messages.success(request, "Profile updated successfully")
            
        return render(request, 'seller_profile.html', {'seller': seller})
        
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def delete_product(request, product_id):
    """Delete a product"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        product = Product.objects.get(id=product_id, seller=seller)
        
        # Delete the product
        product.delete()
        
        messages.success(request, "Product deleted successfully!")
        return redirect('seller_products')
        
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('seller_products')
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def seller_orders(request):
    """View all orders containing seller's products"""
    seller_id = request.session.get('seller_id')
    if not seller_id:
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=seller_id)
        
        # Filter orders by status if provided
        status_filter = request.GET.get('status', '')
        
        # Get all orders containing seller's products
        orders = Order.objects.filter(
            items__product__seller=seller
        ).distinct().order_by('-order_date')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        # Calculate items count for each order
        orders_with_counts = []
        for order in orders:
            seller_item_count = order.items.filter(product__seller=seller).count()
            orders_with_counts.append({
                'order': order,
                'seller_item_count': seller_item_count
            })
        
        # Add pagination
        paginator = Paginator(orders, 10)  # Show 10 orders per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'seller_orders.html', {
            'seller': seller,
            'page_obj': page_obj,
            'orders_with_counts': orders_with_counts,
            'status_filter': status_filter,
            'order_status_choices': Order.ORDER_STATUS_CHOICES
        })
        
    except Seller.DoesNotExist:
        return redirect('seller_logout')

def get_seller_item_count(self, seller_id):
    return self.items.filter(product__seller_id=seller_id).count()