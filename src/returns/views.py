from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from orders.models import Sale, SaleItem
from products.models import Product
from .models import RMA, RMAItem, RMAEvent, RMANotification
from .forms import CreateRMAForm, RMAUpdateForm
from accounts.decorators import admin_required


@login_required
def create_rma(request, sale_id):
    """Create a new RMA request for a sale"""
    sale = get_object_or_404(Sale, id=sale_id, user=request.user)
    
    # Check if ANY RMA already exists for this sale (including closed/cancelled ones)
    existing_rma = RMA.objects.filter(sale=sale, customer=request.user).first()
    if existing_rma:
        if existing_rma.status == 'closed':
            messages.error(request, "A return request for this order was already processed and closed. You cannot create a new return request for this order.")
        else:
            messages.info(request, "A return request for this order already exists.")
        return redirect('returns:rma_detail', rma_id=existing_rma.id)
    
    # Check if sale is eligible for return (e.g., not already fully returned)
    if request.method == 'POST':
        form = CreateRMAForm(request.POST, request.FILES, sale=sale)
        if form.is_valid():
            # Check if at least one item has quantity > 0
            has_items = False
            items_to_create = []
            
            for sale_item in sale.items.all():
                field_name = f'quantity_{sale_item.id}'
                quantity = form.cleaned_data.get(field_name, 0)
                if quantity and quantity > 0:
                    has_items = True
                    items_to_create.append((sale_item, quantity))
            
            if not has_items:
                messages.error(request, "Please select at least one item to return.")
                return render(request, 'returns/returns_create.html', {'form': form, 'sale': sale})
            
            # Create RMA
            with transaction.atomic():
                rma = RMA.objects.create(
                    sale=sale,
                    customer=request.user,
                    reason=form.cleaned_data['reason'],
                    notes=form.cleaned_data['notes']
                )
                
                # Create RMA items
                for sale_item, quantity in items_to_create:
                    RMAItem.objects.create(
                        rma=rma,
                        sale_item=sale_item,
                        requested_quantity=quantity
                    )
                
                # Log initial event
                RMAEvent.objects.create(
                    rma=rma,
                    from_status="",
                    to_status="requested",
                    actor=request.user,
                    notes="RMA request created"
                )
                
                # Auto-transition to "under_review" immediately after creation
                rma.transition_to("under_review", actor=request.user, notes="Request submitted and under review")
            
            messages.success(request, f"RMA #{rma.id} has been created successfully. We'll review your request soon.")
            return redirect('returns:rma_detail', rma_id=rma.id)
    else:
        form = CreateRMAForm(sale=sale)
    
    return render(request, 'returns/returns_create.html', {'form': form, 'sale': sale})


@login_required
def rma_list(request):
    """List all RMAs for the logged-in user"""
    is_admin = (hasattr(request.user, 'profile') and request.user.profile.is_admin) or request.user.is_superuser
    if is_admin:
        # Admins see all RMAs
        rmas = RMA.objects.all().order_by('-opened_at')
    else:
        # Customers see only their RMAs
        rmas = RMA.objects.filter(customer=request.user).order_by('-opened_at')
    
    # Auto-fix: Check and fix any RMAs stuck in "received" status
    stuck_rmas = rmas.filter(status='received')
    for rma in stuck_rmas:
        if rma.can_transition_to('under_inspection'):
            with transaction.atomic():
                rma.transition_to('under_inspection', actor=None, notes='Automatically transitioned from received to under inspection')
    
    is_admin = (hasattr(request.user, 'profile') and request.user.profile.is_admin) or request.user.is_superuser
    return render(request, 'returns/returns_list.html', {
        'rmas': rmas,
        'user_is_admin': is_admin
    })


@login_required
def rma_detail(request, rma_id):
    """View details of a specific RMA"""
    is_admin = (hasattr(request.user, 'profile') and request.user.profile.is_admin) or request.user.is_superuser
    if is_admin:
        rma = get_object_or_404(RMA, id=rma_id)
    else:
        rma = get_object_or_404(RMA, id=rma_id, customer=request.user)
    
    # Auto-fix: If status is "received", automatically transition to "under_inspection"
    if rma.status == 'received' and rma.can_transition_to('under_inspection'):
        with transaction.atomic():
            rma.transition_to('under_inspection', actor=None, notes='Automatically transitioned from received to under inspection')
    
    refund_total = rma.compute_refund_total()
    
    # Get notifications for this RMA
    rma_notifications = RMANotification.objects.filter(rma=rma, user=request.user).order_by('-created_at')
    
    is_admin = (hasattr(request.user, 'profile') and request.user.profile.is_admin) or request.user.is_superuser
    return render(request, 'returns/returns_detail.html', {
        'rma': rma,
        'refund_total': refund_total,
        'user_is_admin': is_admin,
        'rma_notifications': rma_notifications
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def rma_approve(request, rma_id):
    """Validate an RMA request (admin approves/validates)"""
    rma = get_object_or_404(RMA, id=rma_id)
    
    if not rma.can_transition_to("validated"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
        messages.error(request, "Cannot validate RMA in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    # Validate RMA (do not set approved_quantity yet - that happens after inspection)
    with transaction.atomic():
        rma.transition_to("validated", actor=request.user, notes="RMA validated by staff")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'RMA validated successfully'})
    
    messages.success(request, f"RMA #{rma.id} has been validated.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@admin_required
@require_http_methods(["POST"])
def rma_receive(request, rma_id):
    """Mark RMA as received in warehouse (from in_transit status) and auto-transition to under_inspection"""
    rma = get_object_or_404(RMA, id=rma_id)
    
    if not rma.can_transition_to("received"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
        messages.error(request, "Cannot mark RMA as received in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    with transaction.atomic():
        rma.transition_to("received", actor=request.user, notes="Items received in warehouse")
        # Auto-transition to "under_inspection" immediately after received
        rma.transition_to("under_inspection", actor=request.user, notes="Items under inspection")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'RMA marked as received and under inspection'})
    
    messages.success(request, f"RMA #{rma.id} has been marked as received and is now under inspection.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@admin_required
@require_http_methods(["POST"])
def rma_approve_after_inspection(request, rma_id):
    """Approve RMA after inspection (from under_inspection status)"""
    rma = get_object_or_404(RMA, id=rma_id)
    
    if not rma.can_transition_to("approved"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
        messages.error(request, "Cannot approve RMA in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    # Set approved_quantity after inspection (only when actually approving)
    with transaction.atomic():
        for item in rma.items.all():
            if item.approved_quantity is None:
                item.approved_quantity = item.requested_quantity
                item.save()
        
        rma.transition_to("approved", actor=request.user, notes="RMA approved after inspection - waiting for customer resolution choice")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'RMA approved. Customer can now choose resolution.'})
    
    messages.success(request, f"RMA #{rma.id} has been approved. Customer can now choose their preferred resolution.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@admin_required
@require_http_methods(["POST"])
def rma_refund(request, rma_id):
    """Process refund for RMA"""
    rma = get_object_or_404(RMA, id=rma_id)
    
    if not rma.can_transition_to("refunded"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
        messages.error(request, "Cannot process refund in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    with transaction.atomic():
        # Mark sale items as refunded and restock inventory
        for rma_item in rma.items.all():
            sale_item = rma_item.sale_item
            approved_qty = rma_item.approved_quantity or rma_item.requested_quantity
            
            # Restock the product (assuming restockable = True for all products)
            product = sale_item.product
            product.stock_quantity += approved_qty
            product.save()
        
        rma.transition_to("refunded", actor=request.user, notes="Refund processed")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Refund processed successfully'})
    
    messages.success(request, f"Refund for RMA #{rma.id} has been processed.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@admin_required
@require_http_methods(["POST"])
def rma_close(request, rma_id):
    """Close an RMA (from refunded/repaired/replaced status) or Decline Request (from other statuses)"""
    rma = get_object_or_404(RMA, id=rma_id)
    
    # Store current status before transition
    current_status = rma.status
    
    # Determine target status: "closed" for completed RMAs, "declined" for others
    if current_status in ['refunded', 'repaired', 'replaced']:
        target_status = "closed"
        if not rma.can_transition_to("closed"):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
            messages.error(request, "Cannot close RMA in current status.")
            return redirect('returns:rma_detail', rma_id=rma_id)
        notes = f"RMA closed after {current_status}. Further return requests for this order are not allowed."
    else:
        target_status = "declined"
        if not rma.can_transition_to("declined"):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid status transition'}, status=400)
            messages.error(request, "Cannot decline RMA in current status.")
            return redirect('returns:rma_detail', rma_id=rma_id)
        notes = "Return request declined. Further return requests for this order are not allowed."
    
    with transaction.atomic():
        rma.transition_to(target_status, actor=request.user, notes=notes)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if target_status == "closed":
            return JsonResponse({'success': True, 'message': 'RMA closed successfully. Further return requests for this order are not allowed.'})
        else:
            return JsonResponse({'success': True, 'message': 'Return request declined. Further return requests for this order are not allowed.'})
    
    if target_status == "closed":
        messages.success(request, f"RMA #{rma.id} has been closed. Further return requests for this order are not allowed.")
    else:
        messages.success(request, f"Return request #{rma.id} has been declined. Further return requests for this order are not allowed.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@require_http_methods(["POST"])
def rma_cancel_request(request, rma_id):
    """User cancels their return request (from validated status)"""
    rma = get_object_or_404(RMA, id=rma_id, customer=request.user)
    
    if not rma.can_transition_to("request_cancelled"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cannot cancel request in current status'}, status=400)
        messages.error(request, "Cannot cancel request in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    with transaction.atomic():
        rma.transition_to("request_cancelled", actor=request.user, notes="Return request cancelled by customer")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Return request cancelled successfully'})
    
    messages.success(request, f"Return request #{rma.id} has been cancelled.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@require_http_methods(["POST"])
def rma_item_returned(request, rma_id):
    """User marks item as returned (from validated status, transitions to in_transit)"""
    rma = get_object_or_404(RMA, id=rma_id, customer=request.user)
    
    if not rma.can_transition_to("in_transit"):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cannot mark item as returned in current status'}, status=400)
        messages.error(request, "Cannot mark item as returned in current status.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    with transaction.atomic():
        rma.transition_to("in_transit", actor=request.user, notes="Item marked as returned by customer")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Item marked as returned. Waiting for warehouse confirmation.'})
    
    messages.success(request, f"Item marked as returned. We'll confirm receipt once it arrives.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
@require_http_methods(["POST"])
def rma_choose_resolution(request, rma_id):
    """User chooses resolution: Repair, Replacement, or Refund"""
    rma = get_object_or_404(RMA, id=rma_id, customer=request.user)
    
    if rma.status != 'approved':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'RMA must be approved before choosing resolution'}, status=400)
        messages.error(request, "RMA must be approved before choosing resolution.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    resolution = request.POST.get('resolution')
    if resolution not in ['repair', 'replacement', 'refund']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid resolution choice'}, status=400)
        messages.error(request, "Invalid resolution choice.")
        return redirect('returns:rma_detail', rma_id=rma_id)
    
    with transaction.atomic():
        rma.resolution = resolution
        
        # Transition based on resolution choice
        if resolution == 'refund':
            # If refund chosen, process refund immediately
            for rma_item in rma.items.all():
                sale_item = rma_item.sale_item
                approved_qty = rma_item.approved_quantity or rma_item.requested_quantity
                
                # Restock the product
                product = sale_item.product
                product.stock_quantity += approved_qty
                product.save()
            
            rma.transition_to("refunded", actor=request.user, notes=f"Customer chose {resolution.capitalize()} - refund processed")
        elif resolution == 'repair':
            # Transition to repaired status
            rma.transition_to("repaired", actor=request.user, notes=f"Customer chose {resolution.capitalize()} as resolution")
        elif resolution == 'replacement':
            # Transition to replaced status
            rma.transition_to("replaced", actor=request.user, notes=f"Customer chose {resolution.capitalize()} as resolution")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if resolution == 'refund':
            return JsonResponse({'success': True, 'message': f'Refund chosen and processed successfully'})
        else:
            return JsonResponse({'success': True, 'message': f'{resolution.capitalize()} chosen. We will process your request.'})
    
    if resolution == 'refund':
        messages.success(request, f"Refund chosen and processed successfully.")
    else:
        messages.success(request, f"{resolution.capitalize()} chosen. We will process your request.")
    return redirect('returns:rma_detail', rma_id=rma_id)


@login_required
def notification_list(request):
    """Get list of notifications for the current user"""
    notifications = RMANotification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return JsonResponse({
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'status': n.status,
                'status_display': RMANotification.NOTIFICATION_STATUSES.get(n.status, n.status),
                'rma_id': n.rma.id,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ],
        'unread_count': RMANotification.objects.filter(user=request.user, is_read=False).count()
    })


@login_required
@require_http_methods(["POST"])
def notification_mark_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(RMANotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def notification_mark_all_read(request):
    """Mark all notifications as read for the current user"""
    RMANotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({'success': True})

