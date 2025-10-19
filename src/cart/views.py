from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from django.core.cache import cache
from products.models import Product
from products.services import current_effective_price, is_flash_sale_active, validate_price_consistency
from .models import Cart
from .throttle import allow_checkout
from worker.queue import enqueue_job, create_stock_reservation
from retail.logging import (
    log_checkout_requested, log_checkout_throttled, log_checkout_stock_conflict,
    log_checkout_queued, log_price_validation, log_idempotency_check, FlashSaleTimer
)
import re
import json
import uuid
from .forms import CheckoutForm
from orders.models import Sale, SaleItem, Payment
from retail.payment import process_payment
import logging

logger = logging.getLogger(__name__)



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
    
    try:
        cart.add(product, quantity)
        messages.success(request, f'{product.name} added to cart!')
    except ValueError as e:
        messages.error(request, str(e))
    
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
    try:
        cart.update(product, quantity)
        messages.success(request, f'Cart updated!')
    except ValueError as e:
        messages.error(request, str(e))
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
# NEW CHECKOUT VIEW (with concurrency handling)
# -------------------------------
@login_required
def checkout(request):
    cart = Cart(request)
    if cart.get_total_items() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_view")

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        # A1. Form Validation Failure
        if not form.is_valid():
            # Convert form errors to user-friendly messages
            for field, errors in form.errors.items():
                for error in errors:
                    # Extract text content from error (remove HTML tags)
                    error_text = str(error).strip()
                    error_text = re.sub(r'<[^>]+>', '', error_text)
                    messages.error(request, error_text)
            
            return render(
                request,
                "cart/checkout.html",
                {"form": form, "cart_items": list(cart), "total_price": cart.get_total_price()},
            )

        if form.is_valid():
            address = form.cleaned_data["address"]
            payment_method = form.cleaned_data["payment_method"]
            card_number = form.cleaned_data["card_number"]
            total = cart.get_total_price()

            # Step 6: Process payment (mock)
            result = process_payment(payment_method, float(total), card_number)
            if result["status"] != "approved":
                # A4. Payment Failure/Decline - detailed error handling
                reason = result.get("reason", "Unknown error")
                
                if result["status"] == "failed":
                    messages.error(request, f"Payment failed: {reason}. Please check your details and try again.")
                elif result["status"] == "declined":
                    messages.error(request, f"Payment declined: {reason}. Please try a different payment method or contact your bank.")
                else:
                    messages.error(request, "Payment failed. Please try again.")
                
                # Log the payment attempt (in a real system, this would go to a proper logging system)
                # TODO: Implement proper logging system
                return redirect("cart:checkout")

            # Use atomic transaction ONLY for the database operations
            try:
                with transaction.atomic():
                    # Step 7 + 8: Save sale + decrement stock atomically
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
                        # 🔑 Use select_for_update to lock product rows
                        product = Product.objects.select_for_update().get(id=item["product"].id)

                        if product.stock_quantity < item["quantity"]:
                            # 8a. Concurrency conflict: not enough stock at commit
                            raise IntegrityError(f"Insufficient stock for {product.name}")

                        product.stock_quantity -= item["quantity"]
                        product.save()

                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=item["quantity"],
                            unit_price=current_effective_price(product),
                        )

                # Clear cart after successful checkout (OUTSIDE atomic block)
                cart.clear()
                messages.success(request, "Checkout successful! Your order has been placed.")
                return redirect("orders:order_detail", order_id=sale.id)

            except IntegrityError as e:
                # A5. Concurrency Conflict on Stock
                # Log conflict (in real life → monitoring/alert system)
                # TODO: Implement proper logging system

                # Clear the cart (OUTSIDE atomic block - this is now safe)
                cart_cleared = False
                try:
                    # Create a fresh cart instance to ensure we're working with current data
                    fresh_cart = Cart(request)
                    fresh_cart.clear()
                    
                    # Double-check: Force clear cart items directly from database
                    if request.user.is_authenticated:
                        from cart.models import CartItem
                        CartItem.objects.filter(user=request.user).delete()
                    
                    cart_cleared = True
                except Exception as clear_error:
                    cart_cleared = False

                # Extract product name from error message for better user feedback
                error_message = str(e)
                if "Insufficient stock for" in error_message:
                    product_name = error_message.replace("Insufficient stock for ", "")
                    if cart_cleared:
                        user_message = f"Sorry, another customer just purchased the last of '{product_name}'. Your payment has been voided and your cart has been cleared. Please try again later."
                    else:
                        user_message = f"Sorry, another customer just purchased the last of '{product_name}'. Your payment has been voided. Please check your cart and try again later."
                else:
                    if cart_cleared:
                        user_message = "Sorry, another customer just purchased the last of this item. Your payment has been voided and your cart has been cleared. Please try again later."
                    else:
                        user_message = "Sorry, another customer just purchased the last of this item. Your payment has been voided. Please check your cart and try again later."
                
                messages.error(request, user_message)
                
                # Redirect to products page instead of cart view to avoid confusion
                return redirect("products:product_list")

    else:
        form = CheckoutForm()

    # Render checkout form with cart summary
    context = {
        "cart_items": list(cart),
        "total_price": cart.get_total_price(),
        "form": form,
    }
    return render(request, "cart/checkout.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def flash_checkout(request):
    """
    Enhanced flash sale checkout with idempotency, granular throttling, 
    minimal locking, and comprehensive observability.
    """
    # Check global feature flag
    if not settings.FLASH_SALE_ENABLED:
        return JsonResponse({
            "status": "error", 
            "message": "Flash sale is not currently enabled"
        }, status=400)
    
    # Get user identifier for throttling
    user_id = str(request.user.id) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anonymous')
    
    # Extract idempotency key
    idempotency_key = request.headers.get('X-Idempotency-Key')
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())
    
    # Check for duplicate requests using idempotency key
    cache_key = f'flash_checkout_{idempotency_key}'
    existing_result = cache.get(cache_key)
    if existing_result:
        log_idempotency_check(user_id, idempotency_key, True, existing_result.get('sale_id'))
        return JsonResponse(existing_result)
    
    log_idempotency_check(user_id, idempotency_key, False)
    
    try:
        # Parse request data
        data = json.loads(request.body)
        address = data.get('address')
        payment_method = data.get('payment_method')
        card_number = data.get('card_number')
        
        if not address or not payment_method:
            return JsonResponse({
                "status": "error", 
                "message": "Address and payment method are required"
            }, status=400)
        
        # Get cart and validate
        cart = Cart(request)
        if cart.get_total_items() == 0:
            return JsonResponse({
                "status": "error", 
                "message": "Your cart is empty"
            }, status=400)
        
        # Check if cart contains flash sale items
        flash_items = []
        product_ids = []
        for item in cart:
            product_ids.append(item['product'].id)
            if is_flash_sale_active(item['product']):
                flash_items.append(item)
        
        if not flash_items:
            return JsonResponse({
                "status": "error", 
                "message": "No flash sale items in cart"
            }, status=400)
        
        # Granular throttling by user + product
        for item in flash_items:
            allowed, reason, retry_after = allow_checkout(user_id, item['product'].id)
            if not allowed:
                log_checkout_throttled(user_id, reason, retry_after, item['product'].id)
                response = JsonResponse({
                    "status": "throttled", 
                    "message": reason
                }, status=429)
                response['Retry-After'] = str(retry_after)
                return response
        
        # Global throttling
        allowed, reason, retry_after = allow_checkout(user_id)
        if not allowed:
            log_checkout_throttled(user_id, reason, retry_after)
            response = JsonResponse({
                "status": "throttled", 
                "message": reason
            }, status=429)
            response['Retry-After'] = str(retry_after)
            return response
        
        # Calculate total using effective pricing
        total = cart.get_total_price()
        
        # Log checkout request
        log_checkout_requested(user_id, product_ids, float(total), idempotency_key)
        
        # Start timing the sync phase
        with FlashSaleTimer('flash_checkout_sync', user_id, product_ids) as timer:
            with transaction.atomic():
                # Create sale record
                sale = Sale.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    address=address,
                    total=total,
                    status="PENDING",
                )
                
                # Create payment record
                payment = Payment.objects.create(
                    sale=sale,
                    method=payment_method,
                    reference="",
                    amount=total,
                    status="PENDING",
                )
                
                # Process each cart item with minimal locking
                for item in cart:
                    product = Product.objects.select_for_update(of=['self']).get(id=item["product"].id)
                    
                    # Idempotent stock check - verify current available stock
                    if product.stock_quantity < item["quantity"]:
                        raise IntegrityError(f"Insufficient stock for {product.name}")
                    
                    # Create stock reservation
                    create_stock_reservation(sale.id, product.id, item["quantity"])
                    
                    # Decrement stock
                    product.stock_quantity -= item["quantity"]
                    product.save()
                    
                    # Create sale item with effective pricing
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item["quantity"],
                        unit_price=current_effective_price(product),
                    )
                
                # Enqueue finalization job
                job_payload = {
                    'sale_id': sale.id,
                    'payment_method': payment_method,
                    'card_number': card_number,
                    'amount': float(total)
                }
                
                job = enqueue_job('finalize_flash_order', job_payload)
                
                # Clear cart
                cart.clear()
                
                # Calculate sync duration
                sync_duration_ms = (time.monotonic() - timer.start_time) * 1000
                
                # Log successful queuing
                log_checkout_queued(user_id, sale.id, job.id, sync_duration_ms)
                
                # Prepare response
                response_data = {
                    "status": "queued",
                    "reference": str(sale.id),
                    "message": "Your order is being finalized. You will receive confirmation shortly.",
                    "job_id": job.id,
                    "sync_duration_ms": round(sync_duration_ms, 2)
                }
                
                # Cache the result for idempotency
                cache.set(cache_key, response_data, timeout=300)  # 5 minutes
                
                return JsonResponse(response_data)
                
    except IntegrityError as e:
        # Stock conflict - log with detailed information
        product_name = str(e).replace("Insufficient stock for ", "")
        log_checkout_stock_conflict(user_id, None, product_name, 0, 0)
        
        return JsonResponse({
            "status": "error", 
            "message": f"Sorry, another customer just purchased the last of '{product_name}'. Please try again."
        }, status=409)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid JSON data"
        }, status=400)
        
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in flash_checkout: {e}", exc_info=True)
        
        return JsonResponse({
            "status": "error", 
            "message": "An error occurred processing your order"
        }, status=500)
