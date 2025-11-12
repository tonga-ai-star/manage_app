
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from products.models import SanPham
from inventory.models import NhapKho, XuatKho
from partners.models import NhaCungCap


# @login_required
# def dashboard(request):
#     # Thống kê tổng quan
#     total_products = SanPham.objects.count()
#     total_suppliers = NhaCungCap.objects.count()
#     total_customers = KhachHang.objects.count()
#
#     # Thống kê nhập xuất
#     total_imports = NhapKho.objects.count()
#     total_exports = XuatKho.objects.count()
#
#     # Tổng giá trị tồn kho
#     inventory_value = SanPham.objects.aggregate(
#         total_value=Sum('ton_kho')
#     )['total_value'] or 0
#
#     # Doanh thu tháng (giả lập)
#     monthly_revenue = 75000000
#
#     # Dữ liệu biểu đồ
#     chart_data = {
#         'labels': ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6'],
#         'imports': [120, 150, 180, 90, 200, 170],
#         'exports': [80, 100, 120, 110, 150, 130],
#         'inventory': [500, 550, 610, 590, 640, 680]
#     }
#
#     # Đơn hàng gần đây
#     recent_exports = XuatKho.objects.order_by('-ngay_tao')[:5]
#
#     # Sản phẩm tồn kho thấp
#     low_stock = SanPham.objects.filter(ton_kho__lt=10)[:5]
#
#     context = {
#         'total_products': total_products,
#         'total_imports': total_imports,
#         'total_exports': total_exports,
#         'total_suppliers': total_suppliers,
#         'total_customers': total_customers,
#         'inventory_value': inventory_value,
#         'monthly_revenue': monthly_revenue,
#         'chart_data': chart_data,
#         'recent_exports': recent_exports,
#         'low_stock': low_stock,
#     }
#
#     return render(request, 'dashboard.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import NguoiDung
from .forms import NguoiDungForm
from django.shortcuts import redirect
from django.contrib.auth import logout


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
    # DÙNG DỮ LIỆU GIẢ - KHÔNG TRUY VẤN DATABASE
    context = {
        'total_products': 156,
        'total_imports': 23,
        'total_exports': 45,
        'total_suppliers': 8,
        'inventory_value': 125000000,
        'monthly_revenue': 75000000,
        'chart_data': {
            'labels': ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6'],
            'imports': [120, 150, 180, 90, 200, 170],
            'exports': [80, 100, 120, 110, 150, 130],
            'inventory': [500, 550, 610, 590, 640, 680]
        },
        'recent_exports': [
            {'ma_phieu': 'XK-001', 'khach_hang': 'Siêu thị Co.op Mart', 'tong_tien': 1500000},
            {'ma_phieu': 'XK-002', 'khach_hang': 'Circle K', 'tong_tien': 850000},
        ],
        'low_stock': [
            {'ten_san_pham': 'Bút bi đỏ', 'ton_kho': 5},
            {'ten_san_pham': 'Vở 200 trang', 'ton_kho': 8},
        ],
    }
    return render(request, 'dashboard.html', context)

def custom_logout(request):
    logout(request)
    return redirect('login')