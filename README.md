Full Stack Ecommerce Application using Django
# Full Stack Ecommerce Application using Django

A full-featured e-commerce web application built with Django and Django REST Framework.

## Features

- User Signup/Login/Logout  
- Product Listings with Search, Sort, and Filters  
- Add to Cart and Buy Now  
- Razorpay Payment Integration  
- Order History and Checkout  
- Seller Signup and Product Upload  

## Tech Stack

- **Backend**: Django, Django REST Framework  
- **Frontend**: HTML, CSS, JavaScript  
- **Database**: SQLite (default), MySQL/PostgreSQL supported  
- **Payments**: Razorpay  

## Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/your-django-app.git
   cd your-django-app
   ```

2. **Create virtual environment and activate**  
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**  
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**  
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the server**  
   ```bash
   python manage.py runserver
   ```

7. **Access the app**  
   Open your browser and go to:  
   `http://127.0.0.1:8000/`

## API Endpoints

- `/api/products/` – List all products  
- `/api/cart/` – Manage cart  
- `/api/orders/` – View and place orders  
- `/api/payment/` – Razorpay integration  
- `/api/seller/signup/` – Register as seller  

## License

This project is licensed under the MIT License.
