from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

def featured_products(request):
    # Dummy implementation
    context = {
        'title': 'Featured Products',
        'products': [
            {'id': 1, 'name': 'Premium Wireless Earbuds', 'price': 129.99, 'image': 'earbuds.jpg', 'is_featured': True},
            {'id': 2, 'name': 'Smart Watch Series 5', 'price': 249.99, 'image': 'smartwatch.jpg', 'is_featured': True},
            {'id': 3, 'name': '4K Ultra HD TV', 'price': 799.99, 'image': 'tv.jpg', 'is_featured': True},
        ]
    }
    return render(request, 'footerpages/featured_products.html', context)

def deals(request):
    # Dummy implementation
    context = {
        'title': 'Special Deals & Offers',
        'deals': [
            {'id': 1, 'name': 'Summer Sale - 30% off on all audio devices', 'valid_until': 'June 30, 2025'},
            {'id': 2, 'name': 'Buy 2 Get 1 Free on all accessories', 'valid_until': 'May 31, 2025'},
            {'id': 3, 'name': 'Free shipping on orders over $100', 'valid_until': 'Ongoing'},
        ]
    }
    return render(request, 'footerpages/deals.html', context)

def contact(request):
    if request.method == 'POST':
        # Process form submission (dummy implementation)
        messages.success(request, 'Your message has been sent. We will get back to you soon!')
        return redirect('contact')
    
    context = {
        'title': 'Contact Us',
        'contact_info': {
            'address': '123 Tech Street, Digital City, DC 12345',
            'phone': '+1 (555) 123-4567',
            'email': 'support@digivibe.com',
            'hours': 'Monday-Friday: 9am-6pm EST, Saturday: 10am-4pm EST'
        }
    }
    return render(request, 'footerpages/contact.html', context)

def faq(request):
    context = {
        'title': 'Frequently Asked Questions',
        'faqs': [
            {
                'question': 'How long does shipping take?',
                'answer': 'Standard shipping takes 3-5 business days. Express shipping is available for 1-2 business days delivery.'
            },
            {
                'question': 'What is your return policy?',
                'answer': 'We offer a 30-day return policy for most items. Products must be in original condition with all packaging.'
            },
            {
                'question': 'Do you ship internationally?',
                'answer': 'Yes, we ship to most countries. International shipping typically takes 7-14 business days.'
            },
            {
                'question': 'How can I track my order?',
                'answer': 'You will receive a tracking number via email once your order ships. You can also check order status in your account.'
            },
            {
                'question': 'Do you offer warranty on products?',
                'answer': 'Most products come with a 1-year manufacturer warranty. Extended warranties are available for select items.'
            },
        ]
    }
    return render(request, 'footerpages/faq.html', context)

def shipping_policy(request):
    context = {
        'title': 'Shipping Policy',
        'content': """
        <h2>Shipping Policy</h2>
        <p><strong>Processing Time:</strong> Orders are typically processed within 1-2 business days.</p>
        <p><strong>Shipping Options:</strong></p>
        <ul>
            <li>Standard Shipping: 3-5 business days ($5.99 or free on orders over $50)</li>
            <li>Express Shipping: 1-2 business days ($12.99)</li>
            <li>International Shipping: 7-14 business days (varies by location)</li>
        </ul>
        <p><strong>Tracking:</strong> A tracking number will be provided via email once your order ships.</p>
        <p><strong>International Orders:</strong> Please note that customs fees may apply for international orders.</p>
        """
    }
    return render(request, 'footerpages/policy.html', context)

def returns_policy(request):
    context = {
        'title': 'Returns & Refunds Policy',
        'content': """
        <h2>Returns & Refunds Policy</h2>
        <p><strong>Return Period:</strong> 30 days from the date of delivery for most items.</p>
        <p><strong>Return Requirements:</strong></p>
        <ul>
            <li>Items must be in original condition</li>
            <li>Original packaging must be intact</li>
            <li>Receipt or proof of purchase required</li>
        </ul>
        <p><strong>Refund Process:</strong> Refunds will be processed within 5-7 business days after we receive the returned item.</p>
        <p><strong>Exceptions:</strong> Certain items like earbuds, software, and customized products cannot be returned unless defective.</p>
        <p><strong>Defective Items:</strong> Please contact customer support within 48 hours of receiving a defective item.</p>
        """
    }
    return render(request, 'footerpages/policy.html', context)

def privacy_policy(request):
    context = {
        'title': 'Privacy Policy',
        'content': """
        <h2>Privacy Policy</h2>
        <p>Last Updated: April 15, 2025</p>
        
        <h3>1. Information We Collect</h3>
        <p>We collect personal information such as your name, email address, shipping address, payment information, and device information when you use our website.</p>
        
        <h3>2. How We Use Your Information</h3>
        <p>We use your information to process orders, communicate with you about your orders, improve our services, and send promotional materials (if you've opted in).</p>
        
        <h3>3. Cookies and Tracking</h3>
        <p>We use cookies to enhance your browsing experience, analyze site traffic, and personalize content.</p>
        
        <h3>4. Data Sharing</h3>
        <p>We share your information with shipping partners, payment processors, and other service providers as necessary to fulfill orders and provide services.</p>
        
        <h3>5. Your Rights</h3>
        <p>You have the right to access, correct, or delete your personal information. Please contact us at privacy@digivibe.com for assistance.</p>
        """
    }
    return render(request, 'footerpages/policy.html', context)

def terms(request):
    context = {
        'title': 'Terms & Conditions',
        'content': """
        <h2>Terms & Conditions</h2>
        <p>Last Updated: March 30, 2025</p>
        
        <h3>1. Acceptance of Terms</h3>
        <p>By accessing or using DigiVibe's website, you agree to these terms and conditions.</p>
        
        <h3>2. Products and Pricing</h3>
        <p>We reserve the right to modify prices and product availability without notice. All prices are in USD unless otherwise specified.</p>
        
        <h3>3. User Accounts</h3>
        <p>You are responsible for maintaining the confidentiality of your account information and for all activities under your account.</p>
        
        <h3>4. Intellectual Property</h3>
        <p>All content on this website, including logos, images, and text, is the property of DigiVibe and protected by copyright laws.</p>
        
        <h3>5. Limitation of Liability</h3>
        <p>DigiVibe shall not be liable for any indirect, incidental, special, or consequential damages resulting from the use or inability to use our products or services.</p>
        
        <h3>6. Governing Law</h3>
        <p>These terms shall be governed by the laws of the state of California, without regard to its conflict of law provisions.</p>
        """
    }
    return render(request, 'footerpages/policy.html', context)

def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # In a real application, you would save this to a database
        # For now, just show a success message
        messages.success(request, f'Thank you for subscribing to our newsletter with {email}!')
        return redirect('home')
    return redirect('home')

def social_redirect(request, platform):
    # Dummy implementation - in a real app, you would redirect to actual social media pages
    social_urls = {
        'facebook': 'https://facebook.com/digivibe',
        'twitter': 'https://twitter.com/digivibe',
        'instagram': 'https://instagram.com/digivibe',
        'youtube': 'https://youtube.com/digivibe',
    }
    
    if platform in social_urls:
        return redirect(social_urls[platform])
    return redirect('home')