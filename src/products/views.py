from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.conf import settings
from .models import Product, Category
from .forms import ProductForm, ProductSearchForm, CategoryForm
from .services import is_flash_sale_active, current_effective_price
from accounts.decorators import admin_required
from cart.models import Cart


@login_required
def product_list(request):
    """Display list of products with search and filter functionality"""
    products = Product.objects.all()
    search_form = ProductSearchForm(request.GET)
    
    # Determine low-stock threshold (configurable)
    try:
        threshold = int(request.GET.get("low_stock_threshold", settings.LOW_STOCK_THRESHOLD_DEFAULT))
        if threshold < 0:
            threshold = settings.LOW_STOCK_THRESHOLD_DEFAULT
    except (TypeError, ValueError):
        threshold = settings.LOW_STOCK_THRESHOLD_DEFAULT
    
    # Whether to show only low-stock products
    only_low_stock = request.GET.get("only_low_stock") == "on"
    
    # Check if user can manage products (same logic as user_is_admin context processor)
    can_manage_products = False
    if request.user.is_authenticated:
        # Superusers automatically have admin access
        if request.user.is_superuser:
            can_manage_products = True
        # Check if user has profile and is admin
        elif hasattr(request.user, 'profile'):
            can_manage_products = request.user.profile.is_admin
    
    # Apply search filter
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        stock_status = search_form.cleaned_data.get('stock_status')
        
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            products = products.filter(category=category)
        
        if stock_status:
            if stock_status == 'in_stock':
                products = products.filter(stock_quantity__gt=10)
            elif stock_status == 'low_stock':
                products = products.filter(stock_quantity__gt=0, stock_quantity__lte=10)
            elif stock_status == 'out_of_stock':
                products = products.filter(stock_quantity=0)
            elif stock_status == 'flash_sale':
                # Filter for products that are currently on flash sale
                from django.utils import timezone
                now = timezone.now()
                products = products.filter(
                    flash_sale_enabled=True,
                    flash_sale_price__isnull=False,
                    flash_sale_starts_at__isnull=False,
                    flash_sale_ends_at__isnull=False,
                    flash_sale_starts_at__lte=now,
                    flash_sale_ends_at__gte=now
                )
    else:
        # If form is invalid, don't apply any filters (show all products)
        pass
    
    # Additional low-stock filter for admin: only show products below dynamic threshold
    if can_manage_products and only_low_stock:
        products = products.filter(stock_quantity__gt=0, stock_quantity__lte=threshold)
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get cart information for order summary
    cart = Cart(request)
    cart_items = list(cart)
    cart_total_price = cart.get_total_price()
    cart_total_items = cart.get_total_items()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_products': products.count(),
        'cart_items': cart_items,
        'cart_total_price': cart_total_price,
        'cart_total_items': cart_total_items,
        'low_stock_threshold': threshold,
        'only_low_stock': only_low_stock,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    """Display detailed view of a single product"""
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
    }
    return render(request, 'products/product_detail.html', context)


@admin_required
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'✅ Product "{product.name}" created successfully!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Create New Product',
    }
    return render(request, 'products/product_form.html', context)


@admin_required
def product_update(request, pk):
    """Update an existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'✅ Product "{product.name}" updated successfully!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'title': f'Update {product.name}',
        'product': product,
    }
    return render(request, 'products/product_form.html', context)


@admin_required
def product_delete(request, pk):
    """Delete a product (or deactivate if it has orders)"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        
        try:
            # Try to delete the product
            product.delete()
            messages.success(request, f'✅ Product "{product_name}" deleted successfully!')
        except ProtectedError:
            # If deletion fails (due to protected foreign keys), deactivate instead
            product.is_active = False
            product.save()
            messages.warning(request, f'⚠️ Product "{product_name}" could not be deleted because it has been ordered. It has been deactivated instead.')
        
        return redirect('products:product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)


@admin_required
def category_list(request):
    """Display list of categories"""
    categories = Category.objects.all()
    
    # Handle search
    search_query = request.GET.get('search')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'categories': categories,
    }
    return render(request, 'products/category_list.html', context)


@admin_required
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✅ Category "{category.name}" created successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Create New Category',
    }
    return render(request, 'products/category_form.html', context)


@admin_required
def category_update(request, pk):
    """Update an existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✅ Category "{category.name}" updated successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'title': f'Update {category.name}',
        'category': category,
    }
    return render(request, 'products/category_form.html', context)


@admin_required
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'✅ Category "{category_name}" deleted successfully!')
        return redirect('products:category_list')
    
    context = {
        'category': category,
    }
    return render(request, 'products/category_confirm_delete.html', context)


def flash_sale_status(request, product_id):
    """Get flash sale status for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    active = is_flash_sale_active(product)
    effective_price = current_effective_price(product)
    
    response_data = {
        'active': active,
        'effective_price': float(effective_price),
        'regular_price': float(product.price),
        'flash_sale_price': float(product.flash_sale_price) if product.flash_sale_price else None,
        'starts_at': product.flash_sale_starts_at.isoformat() if product.flash_sale_starts_at else None,
        'ends_at': product.flash_sale_ends_at.isoformat() if product.flash_sale_ends_at else None,
        'stock_quantity': product.stock_quantity,
        'is_in_stock': product.is_in_stock,
    }
    
    return JsonResponse(response_data)
