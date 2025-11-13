
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import NguoiDung
from .forms import NguoiDungForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField
from products.models import SanPham
from inventory.models import NhapKho, XuatKho, TonKho
from partners.models import NhaCungCap



@login_required
def danh_sach_nhan_vien(request):
    nhan_vien_list = NguoiDung.objects.filter(vai_tro__in=['staff', 'manager'])

    # --- Lấy tham số tìm kiếm & lọc ---
    q = request.GET.get('q', '').strip()
    vai_tro = request.GET.get('vai_tro', '')
    trang_thai = request.GET.get('trang_thai', '')

    # --- Tìm kiếm ---
    if q:
        nhan_vien_list = nhan_vien_list.filter(
            Q(ho_ten__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )

    # --- Lọc theo vai trò ---
    if vai_tro:
        nhan_vien_list = nhan_vien_list.filter(vai_tro=vai_tro)

    # --- Lọc theo trạng thái ---
    if trang_thai:
        nhan_vien_list = nhan_vien_list.filter(trang_thai=(trang_thai == 'true'))

    # --- Sắp xếp mới nhất ---
    nhan_vien_list = nhan_vien_list.order_by('-date_joined')

    # --- Thống kê ---
    tong_nhan_vien = nhan_vien_list.count()
    nhan_vien_dang_lam = nhan_vien_list.filter(trang_thai=True).count()
    nhan_vien_nghi_viec = nhan_vien_list.filter(trang_thai=False).count()

    # --- Gửi dữ liệu qua template ---
    context = {
        'nhan_vien_list': nhan_vien_list,
        'tong_nhan_vien': tong_nhan_vien,
        'nhan_vien_dang_lam': nhan_vien_dang_lam,
        'nhan_vien_nghi_viec': nhan_vien_nghi_viec,

        # giữ lại giá trị lọc & tìm kiếm trong form
        'search_query': q,
        'selected_vai_tro': vai_tro,
        'selected_trang_thai': trang_thai,
    }

    return render(request, 'accounts/danh_sach_nhan_vien.html', context)


@login_required
def them_nhan_vien(request):
    if request.method == 'POST':
        form = NguoiDungForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password('123456')  # Mật khẩu mặc định
            user.save()
            messages.success(request, 'Thêm nhân viên thành công!')
            return redirect('danh_sach_nhan_vien')
    else:
        form = NguoiDungForm()

    context = {
        'form': form,
        'title': 'Thêm nhân viên mới'
    }
    return render(request, 'accounts/them_nhan_vien.html', context)


@login_required
def chi_tiet_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    context = {
        'nhan_vien': nhan_vien
    }
    return render(request, 'accounts/chi_tiet_nhan_vien.html', context)


@login_required
def sua_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    if request.method == 'POST':
        form = NguoiDungForm(request.POST, instance=nhan_vien)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thông tin nhân viên thành công!')
            return redirect('danh_sach_nhan_vien')
    else:
        form = NguoiDungForm(instance=nhan_vien)

    context = {
        'form': form,
        'nhan_vien': nhan_vien,
        'title': 'Sửa thông tin nhân viên'
    }
    return render(request, 'accounts/them_nhan_vien.html', context)


@login_required
def xoa_nhan_vien(request, nhan_vien_id):
    nhan_vien = get_object_or_404(NguoiDung, id=nhan_vien_id)

    if nhan_vien.id == request.user.id:
        messages.error(request, 'Không thể xóa chính tài khoản của bạn!')
    else:
        nhan_vien.delete()
        messages.success(request, 'Đã xóa nhân viên thành công!')

    return redirect('danh_sach_nhan_vien')


@login_required
def dashboard(request):
    # --- 1. Tổng quan ---
    total_products = SanPham.objects.count()
    total_suppliers = NhaCungCap.objects.count()
    total_imports = NhapKho.objects.count()
    total_exports = XuatKho.objects.count()

    # --- 2. Tổng tồn kho ---
    total_inventory = TonKho.objects.aggregate(t=Sum('so_luong_ton'))['t'] or 0

    # --- 3. Tổng giá trị tồn kho ---
    inventory_value = TonKho.objects.aggregate(
        total_value=Sum(F('so_luong_ton') * F('san_pham__gia_ban'))
    )['total_value'] or 0

    # --- 4. Top sản phẩm tồn nhiều nhất ---
    top_products = (
        TonKho.objects.select_related('san_pham')
        .values('san_pham__ten_san_pham')
        .annotate(tong_ton=Sum('so_luong_ton'))
        .order_by('-tong_ton')[:5]
    )

    # --- 5. Sản phẩm sắp hết hàng ---
    low_stock = (
        TonKho.objects.select_related('san_pham')
        .filter(so_luong_ton__lte=5)
        .order_by('so_luong_ton')[:5]
    )

    # --- 6. Biểu đồ nhập - xuất theo tháng ---
    nhap_theo_thang = (
        NhapKho.objects.values('ngay_tao__month')
        .annotate(tong=Sum('tong_tien'))
        .order_by('ngay_tao__month')
    )
    xuat_theo_thang = (
        XuatKho.objects.values('ngay_tao__month')
        .annotate(tong=Sum('tong_tien'))
        .order_by('ngay_tao__month')
    )

    labels = [f"Tháng {item['ngay_tao__month']}" for item in nhap_theo_thang]
    import_data = [item['tong'] for item in nhap_theo_thang]
    export_data = [item['tong'] for item in xuat_theo_thang]

    # --- 7. Biểu đồ công nợ nhà cung cấp ---
    cong_no_data = (
        NhaCungCap.objects.values('ten_nha_cung_cap')
        .annotate(tong_no=Sum('tong_no'))
        .order_by('-tong_no')[:5]
        if 'tong_no' in [f.name for f in NhaCungCap._meta.get_fields()]
        else []
    )

    debt_labels = [item['ten_nha_cung_cap'] for item in cong_no_data]
    debt_values = [item['tong_no'] for item in cong_no_data]

    # --- 8. Gửi dữ liệu sang template ---
    context = {
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'total_imports': total_imports,
        'total_exports': total_exports,
        'total_inventory': total_inventory,
        'inventory_value': inventory_value,
        'top_products': top_products,
        'low_stock': low_stock,
        'labels': labels,
        'import_data': import_data,
        'export_data': export_data,
        'debt_labels': debt_labels,
        'debt_values': debt_values,
    }

    return render(request, 'dashboard.html', context)
