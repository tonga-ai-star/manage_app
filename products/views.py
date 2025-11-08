from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SanPham
from .forms import SanPhamForm

@login_required
def product_list(request):
    products = SanPham.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        form = SanPhamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = SanPhamForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Thêm sản phẩm'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(SanPham, pk=pk)
    if request.method == 'POST':
        form = SanPhamForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = SanPhamForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Chỉnh sửa sản phẩm'})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(SanPham, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
@login_required
def category_list(request):
    categories = [
        {'id': 1, 'name': 'Xi măng'},
        {'id': 2, 'name': 'Cát đá'},
        {'id': 3, 'name': 'Thép'},
        {'id': 4, 'name': 'Gạch ống'},
    ]
    return render(request, 'products/category_list.html', {'categories': categories})
def unit_list(request):
    units = [
        {'id': 1, 'name': 'Bao'},
        {'id': 2, 'name': 'Kg'},
        {'id': 3, 'name': 'Tấn'},
        {'id': 4, 'name': 'Khối'},
        {'id': 5, 'name': 'Viên'},
    ]
    return render(request, 'products/unit_list.html', {'units': units})