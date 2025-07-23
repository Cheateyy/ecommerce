from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Address
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.db.models import Q

# Create your views here.
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
    
        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, f'That username {username} is already taken')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.error(request, f'That email {email} is already taken')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_active = False
                user.save()
                # verification section

                # generate UID and token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                # Build activation link
                activation_link = request.build_absolute_uri(reverse('activate', args=[uid,token]))
                # send email
                send_mail(
                    subject = "Verify your email",
                    message = f"Hi {user.username}, \n\n"
                              f"Please click the link below to verify your account\n\n"
                              f"{activation_link}\n\n"
                              ,
                              from_email= None,
                              recipient_list = [user.email],
                )

                messages.success(request, 'Your account has been created, please check your email to verify it')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
    else:
        return render(request, 'accounts/register.html', {'user': request.user})


def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        user = None
        # Try to find user by username or email
        try:
            user_obj = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in')
            return redirect('core-home')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'accounts/login.html', {'user': request.user})   
    
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('core-home')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


def profile_update(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        user = request.user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, 'Your profile has been updated')
        return redirect('profile')
    else:
        return render(request, 'accounts/profile_update.html', {'user': request.user})


def profile_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('password2')           
        
        if password == password2:
            user = request.user
            user.set_password(password)
            user.save()
            messages.success(request, 'Your password has been updated')
            return redirect('profile')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('profile_password')
    else:
        return render(request, 'accounts/profile_password.html', {'user': request.user})


def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted')
        return redirect('core-home')
    else:
        return render(request, 'accounts/profile_delete.html', {'user': request.user})


@login_required
def addresses(request):
    """Display user's addresses"""
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {
        'addresses': addresses,
        'user': request.user
    })

@login_required
def address_add(request):
    """Add a new address"""
    if request.method == 'POST':
        # Create new address
        address = Address.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone'),
            street_address=request.POST.get('street_address'),
            apartment=request.POST.get('apartment'),
            city=request.POST.get('city'),
            zip_code=request.POST.get('zip_code'),
            is_default=request.POST.get('is_default') == 'on',
            is_billing=request.POST.get('is_billing') == 'on',
            is_shipping=request.POST.get('is_shipping') == 'on'
        )
        messages.success(request, 'Address added successfully!')
        return redirect('addresses')
    
    return render(request, 'accounts/address_add.html', {'user': request.user})

@login_required
def address_edit(request, address_id):
    """Edit an existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Update address
        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.phone = request.POST.get('phone')
        address.street_address = request.POST.get('street_address')
        address.apartment = request.POST.get('apartment')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.zip_code = request.POST.get('zip_code')
        address.country = request.POST.get('country', 'United States')
        address.is_default = request.POST.get('is_default') == 'on'
        address.is_billing = request.POST.get('is_billing') == 'on'
        address.is_shipping = request.POST.get('is_shipping') == 'on'
        address.save()
        
        messages.success(request, 'Address updated successfully!')
        return redirect('addresses')
    
    return render(request, 'accounts/address_edit.html', {
        'address': address,
        'user': request.user
    })

@login_required
def address_delete(request, address_id):
    """Delete an address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('addresses')
    
    return render(request, 'accounts/address_delete.html', {
        'address': address,
        'user': request.user
    })

@login_required
def address_set_default(request, address_id):
    """Set an address as default"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, 'Default address updated!')
    return redirect('addresses')

def activate(request, uidb64, token):
    try :
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, User.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated! You may now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return render(request, 'accounts/activation_invalid.html')