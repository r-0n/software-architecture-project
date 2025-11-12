from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Sale, SaleItem, Payment
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime


@login_required
def order_history(request):
    sales = Sale.objects.filter(user=request.user).order_by("-created_at")
    # Check for existing RMAs for each sale (including closed ones - block new requests)
    from returns.models import RMA
    sales_with_rma_info = []
    for sale in sales:
        # Check for any RMA (active or closed) - if any exists, block new requests
        existing_rma = RMA.objects.filter(sale=sale, customer=request.user).first()
        
        # Determine return request status
        return_status = None
        if existing_rma:
            if existing_rma.status == 'declined':
                return_status = 'declined'
            elif existing_rma.status == 'closed':
                return_status = 'closed'
            elif existing_rma.status == 'request_cancelled':
                return_status = 'cancelled'
            elif existing_rma.status == 'repaired':
                return_status = 'repaired'
            elif existing_rma.status == 'replaced':
                return_status = 'replaced'
            elif existing_rma.status == 'refunded':
                return_status = 'refunded'
            elif existing_rma.status in ['validated', 'in_transit', 'received', 'under_inspection', 'approved']:
                return_status = 'in_process'
            else:  # requested, under_review
                return_status = 'in_process'
        
        # Check if closed RMA was refunded (for Status column display)
        was_refunded = False
        if existing_rma and existing_rma.status == 'closed':
            # Check if resolution was refund (customer chose refund, which transitions to refunded then closed)
            was_refunded = existing_rma.resolution == 'refund'
        
        sales_with_rma_info.append({
            'sale': sale,
            'has_active_rma': existing_rma is not None,
            'existing_rma_id': existing_rma.id if existing_rma else None,
            'return_status': return_status,
            'was_refunded': was_refunded
        })
    return render(request, "orders/order_history.html", {"orders_with_rma": sales_with_rma_info})


@login_required
def order_detail(request, order_id):
    sale = get_object_or_404(Sale, id=order_id, user=request.user)
    # Check if ANY RMA already exists for this sale (including closed ones - block new requests)
    from returns.models import RMA
    existing_rma = RMA.objects.filter(sale=sale, customer=request.user).first()
    return render(request, "orders/order_detail.html", {
        "order": sale,
        "has_active_rma": existing_rma is not None,
        "existing_rma_id": existing_rma.id if existing_rma else None
    })


@login_required
def download_receipt(request, order_id):
    """Generate and download PDF receipt for an order"""
    sale = get_object_or_404(Sale, id=order_id, user=request.user)
    
    # Create a BytesIO buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("RETAIL MANAGEMENT SYSTEM", title_style))
    story.append(Paragraph("ORDER RECEIPT", title_style))
    story.append(Spacer(1, 20))
    
    # Order Information
    story.append(Paragraph("Order Information", heading_style))
    
    # Convert UTC timestamp to Dubai timezone for display
    dubai_time = timezone.localtime(sale.created_at, timezone.get_current_timezone())
    
    # Get payment information
    try:
        payment = sale.payment
        payment_method = payment.get_method_display()
        payment_reference = payment.reference or "N/A"
    except Payment.DoesNotExist:
        payment_method = "N/A"
        payment_reference = "N/A"

    order_info = [
        ["Sale ID:", f"#{sale.id}"],
        ["Date:", dubai_time.strftime("%Y-%m-%d %H:%M")],
        ["Status:", sale.status],
        ["Payment Method:", payment_method],
        ["Payment Reference:", payment_reference],
        ["Delivery Address:", sale.address],
    ]
    
    order_table = Table(order_info, colWidths=[2*inch, 4*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(order_table)
    story.append(Spacer(1, 20))
    
    # Items Table
    story.append(Paragraph("Order Items", heading_style))
    
    # Table data
    items_data = [["Product", "Quantity", "Unit Price", "Subtotal"]]
    for item in sale.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.subtotal():.2f}"
        ])

    # Add total row
    items_data.append(["", "", "TOTAL:", f"${sale.total:.2f}"])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 30))
    
    # Footer
    story.append(Paragraph("Thank you for your business!", normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_sale_{sale.id}.pdf"'
    response.write(pdf)
    
    return response
