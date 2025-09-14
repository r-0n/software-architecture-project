from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from products.models import Product
from .models import Cart
import re


#for checkout
from django.db import transaction
from .forms import CheckoutForm
from orders.models import Sale, SaleItem, Payment # new models
from retail.payment import process_payment #new payment service



def cart_view(request):
    """Display shopping cart"""
    cart = Cart(request)
    context = {
        'cart': cart,
        'cart_items': list(cart),
        'total_price': cart.get_total_price(),
        'total_items': cart.get_total_items(),
    }
    return render(request, 'cart/cart.html', context)


def cart_add(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if not product.is_active:
        messages.error(request, 'This product is not available for purchase.')
        return redirect('products:product_detail', pk=product_id)
    
    cart = Cart(request)
    
    # Check current quantity in cart
    current_quantity = 0
    if request.user.is_authenticated:
        # For logged-in users, check database cart
        try:
            from cart.models import CartItem
            cart_item = CartItem.objects.get(product=product, user=request.user)
            current_quantity = cart_item.quantity
        except CartItem.DoesNotExist:
            current_quantity = 0
    else:
        # For anonymous users, check session cart
        if str(product.id) in cart.cart:
            current_quantity = cart.cart[str(product.id)]['quantity']
    
    # Check if total quantity (current + new) exceeds stock
    total_quantity = current_quantity + quantity
    if total_quantity > product.stock_quantity:
        available_to_add = product.stock_quantity - current_quantity
        if available_to_add <= 0:
            messages.error(request, f'Cannot add more {product.name}! You already have all {product.stock_quantity} available items in your cart. Please remove some items first or check back later for restocking.')
        else:
            messages.error(request, f'⚠️ Cannot add {quantity} more {product.name}(s). You can only add {available_to_add} more (you have {current_quantity} in cart, {product.stock_quantity} total available).')
        return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))
    
    cart.add(product, quantity)
    messages.success(request, f'{product.name} added to cart!')
    
    # Redirect back to the page they came from
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def cart_remove(request, product_id):
    """Remove product from cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.success(request, f'{product.name} removed from cart!')
    return redirect('cart:cart_view')


def cart_update(request, product_id):
    """Update product quantity in cart"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > product.stock_quantity:
        messages.error(request, f'⚠️ Cannot update quantity to {quantity}. Only {product.stock_quantity} {product.name}(s) available in stock. Please reduce the quantity.')
        return redirect('cart:cart_view')
    
    cart = Cart(request)
    cart.update(product, quantity)
    messages.success(request, f'Cart updated!')
    return redirect('cart:cart_view')


def cart_clear(request):
    """Clear entire cart"""
    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared!')
    
    # Redirect back to the page they came from, default to products page
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def cart_count(request):
    """API endpoint to get cart item count (for AJAX)"""
    cart = Cart(request)
    return JsonResponse({'count': cart.get_total_items()})


# -------------------------------
# NEW CHECKOUT VIEW
# -------------------------------
@login_required
@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if cart.get_total_items() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_view")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if not form.is_valid():
            # Debug: Print form errors to console
            print(f"Form validation failed: {form.errors}")
            
            # Convert form errors to toast notifications
            for field, errors in form.errors.items():
                print(f"Field: {field}, Errors: {errors}")
                for error in errors:
                    # Extract text content from error (remove HTML tags)
                    error_text = str(error).strip()
                    # Remove any HTML tags if present
                    error_text = re.sub(r'<[^>]+>', '', error_text)
                    error_message = f"❌ {error_text}"
                    print(f"Adding error message: {error_message}")
                    messages.error(request, error_message)
            
            return render(request, "cart/checkout.html", {"form": form, "cart_items": list(cart), "total_price": cart.get_total_price()})
        
        if form.is_valid():
            address = form.cleaned_data["address"]
            payment_method = form.cleaned_data["payment_method"]
            card_number = form.cleaned_data["card_number"]
            total = cart.get_total_price()

            # Step 6: Process payment
            result = process_payment(payment_method, float(total), card_number)
            if result["status"] != "approved":
                # A4. Payment Failure/Decline - detailed error handling
                reason = result.get("reason", "Unknown error")
                
                if result["status"] == "failed":
                    messages.error(request, f"❌ Payment failed: {reason}. Please check your details and try again.")
                elif result["status"] == "declined":
                    messages.error(request, f"❌ Payment declined: {reason}. Please try a different payment method or contact your bank.")
                else:
                    messages.error(request, "❌ Payment failed. Please try again.")
                
                # Log the payment attempt (in a real system, this would go to a proper logging system)
                print(f"Payment attempt failed - Method: {payment_method}, Amount: ${total}, Status: {result['status']}, Reason: {reason}")
                return redirect("cart:checkout")

            # Step 7 + 8: Save sale + decrement stock
            sale = Sale.objects.create(
                user=request.user,
                address=address,
                total=total,
                status="COMPLETED",
            )

            # Create payment record
            Payment.objects.create(
                sale=sale,
                method=payment_method,
                reference=result["reference"],
                amount=total,
                status="COMPLETED",
            )

            for item in cart:
                product = Product.objects.select_for_update().get(id=item["product"].id)
                if product.stock_quantity < item["quantity"]:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect("cart:cart_view")

                product.stock_quantity -= item["quantity"]
                product.save()

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.price,
                )

            cart.clear()
            messages.success(request, "Checkout successful! Your order has been placed.")
            return redirect("orders:order_detail", order_id=sale.id)
    else:
        form = CheckoutForm()

    context = {
        "cart_items": list(cart),
        "total_price": cart.get_total_price(),
        "form": form,
    }
    return render(request, "cart/checkout.html", context)
