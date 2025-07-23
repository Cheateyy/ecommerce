from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, Order, OrderItem
from .forms import CheckoutForm
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import mail_admins

def product_list(request):
    """Display all products with filtering and pagination"""
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Category filtering
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    """Display individual product details"""
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(pk=pk)[:4]  # 4 related products
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def category_detail(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'sort_by': sort_by,
    }
    return render(request, 'products/category_detail.html', context)

def search_products(request):
    """Search products"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(available=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'results_count': products.count(),
    }
    return render(request, 'products/search_results.html', context)

def cart_detail(request):
    """Display the shopping cart with real data from the session"""
    cart = request.session.get('cart', {})  # Get cart from session, or empty dict
    cart_items = []
    total = 0
    total_quantity = 0

    # Fetch product info for each item in the cart
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id, available=True)
            quantity = item.get('quantity', 1)
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
            total += subtotal
            total_quantity += quantity
        except Product.DoesNotExist:
            continue  # Skip products that no longer exist or are unavailable

    context = {
        'cart_items': cart_items,
        'total': total,
        'total_quantity': total_quantity,
    }
    return render(request, 'products/cart_detail.html', context)

def cart_add(request, product_id):
    """Add a product to the cart (session-based)"""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    # If the product is already in the cart, increment the quantity
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += 1
    else:
        cart[product_id_str] = {'quantity': 1}

    request.session['cart'] = cart  # Save cart back to session
    next_url = request.META.get('HTTP_REFERER', None)
    if next_url:
        return redirect(next_url)
    return redirect('cart_detail')

def cart_remove(request, product_id):
    """Remove a product from the cart"""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
    return redirect('cart_detail')

def cart_clear(request):
    """Clear the cart"""
    request.session['cart'] = {}
    return redirect('cart_detail')

def checkout(request):
    """Process the checkout"""
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to checkout')
        return redirect('login')
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            address = form.cleaned_data.get('address')
            if not address:
                form.add_error('address', 'You must select a shipping address.')
                return render(request, 'products/checkout.html', {'form': form, 'cart': cart})

            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user

                total = 0
                cart_items = []
                product_ids = [int(pid) for pid in cart.keys()]
                products = Product.objects.select_for_update().filter(pk__in=product_ids)
                product_map = {product.pk: product for product in products}
                # the dictionary above, contains a the products that are in the order
                for product_id_str, item in cart.items():
                    product_id = int(product_id_str)
                    product = product_map.get(product_id)
                    if not product:
                        continue
                    quantity = item.get('quantity', 1)
                    if product.stock < quantity:
                        form.add_error(None, f"Not enough stock for {product.name}.")
                        return render(request, 'products/checkout.html', {'form': form, 'cart': cart})
                    total += product.price * quantity
                    cart_items.append((product, quantity))

                order.total = total
                order.save()

                # send email
                subject = f"Order Confirmation - Order #{order.id}"
                message = render_to_string('products/email_order_confirmation.txt', {
                    'user': request.user,
                    'order': order,
                    'cart_items': cart_items,
                })
                recipient_list = [request.user.email]
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

                # send email to admins
                admin_subject = f"New Order Placed - Order #{order.id}"
                admin_message = render_to_string('products/email_admin_new_order.txt', {
                    'user': request.user,
                    'order': order,
                    'cart_items': cart_items,
                })
                mail_admins(admin_subject, admin_message)
                # send 
                for product, quantity in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    product.stock = max(product.stock - quantity, 0)
                    product.save()

                request.session['cart'] = {}
                return redirect('checkout_success', order_id=order.id)
    else:
        form = CheckoutForm(user=request.user)
    # Rebuild cart_items and total for GET or invalid POST
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            quantity = item.get('quantity', 1)
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
            total += subtotal
        except Product.DoesNotExist:
            continue
    return render(request, 'products/checkout.html', {'form': form, 'cart': cart, 'cart_items': cart_items, 'total': total})

def checkout_success(request, order_id=None):
    """Display the order confirmation page after successful checkout"""
    order = None
    if order_id:
        from .models import Order
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            order = None
    return render(request, 'products/checkout_success.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user = request.user)
    return render(request, 'products/order_history.html', {'orders' : orders})