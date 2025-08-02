from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q

from .models import Product, Order, OrderItem
from .forms import RegisterForm

# 🛍️ Product Listing + Enhanced Search
def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ) if query else Product.objects.all()

    return render(request, 'store/product_list.html', {
        'products': products,
        'search_active': bool(query),
        'query': query
    })

# ➕ Add to Cart
@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('product_list')

# 🛒 View Cart
@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_total = product.price * qty
        cart_items.append({
            'product': product,
            'quantity': qty,
            'item_total': item_total
        })
        total += item_total

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

# 🔁 Update Quantity
@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            new_quantity = 1

        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if new_quantity > 0:
            cart[product_id_str] = new_quantity
        else:
            cart.pop(product_id_str, None)

        request.session['cart'] = cart

    return redirect('view_cart')

# ❌ Remove from Cart
@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('view_cart')

# 🧹 Clear Cart
@login_required
def clear_cart(request):
    request.session['cart'] = {}
    return redirect('view_cart')

# 💳 Checkout
@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect('view_cart')

    cart_items = []
    total = 0

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_total = product.price * qty
        cart_items.append({
            'product': product,
            'quantity': qty,
            'item_total': item_total
        })
        total += item_total

    if request.method == 'POST':
        # Save order
        order = Order.objects.create(user=request.user, total=total)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
        # Clear cart
        request.session['cart'] = {}
        return render(request, 'store/order_complete.html', {
            'cart_items': cart_items,
            'total': total,
        })

    # ✅ FINAL RETURN BLOCK — You asked to make sure it's here:
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

# 📦 View My Orders
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

# 👤 Register User
def register_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})