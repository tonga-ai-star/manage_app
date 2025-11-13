
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import NguoiDung
from .forms import NguoiDungForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from products.models import SanPham
from inventory.models import NhapKho, XuatKho, TonKho
from partners.models import NhaCungCap
from django.db.models.functions import ExtractMonth
from datetime import datetime

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
    try:
        inventory_value = TonKho.objects.aggregate(
            total_value=Sum(F('so_luong_ton') * F('san_pham__gia_ban'))
        )['total_value'] or 0
    except:
        inventory_value = 0

    # --- 4. Top sản phẩm tồn nhiều nhất ---
    top_products = (
        TonKho.objects.select_related('san_pham')
        .values('san_pham__ten_san_pham', 'san_pham__id')
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
    current_year = datetime.now().year

    nhap_theo_thang = (
        NhapKho.objects.filter(ngay_tao__year=current_year)
        .annotate(month=ExtractMonth('ngay_tao'))
        .values('month')
        .annotate(tong=Sum('tong_tien'))
        .order_by('month')
    )

    xuat_theo_thang = (
        XuatKho.objects.filter(ngay_tao__year=current_year)
        .annotate(month=ExtractMonth('ngay_tao'))
        .values('month')
        .annotate(tong=Sum('tong_tien'))
        .order_by('month')
    )

    # Tạo dữ liệu cho 12 tháng
    labels = [f"Tháng {i}" for i in range(1, 13)]
    import_data = [0] * 12
    export_data = [0] * 12

    for item in nhap_theo_thang:
        month_index = item['month'] - 1
        if 0 <= month_index < 12:
            import_data[month_index] = float(item['tong'] or 0)

    for item in xuat_theo_thang:
        month_index = item['month'] - 1
        if 0 <= month_index < 12:
            export_data[month_index] = float(item['tong'] or 0)
    # --- 7. THÔNG TIN CÔNG NỢ - CÁCH 2 ---
    try:
        # Lọc theo tháng
        selected_month = request.GET.get('month')
        if selected_month:
            selected_month = int(selected_month)
        else:
            selected_month = datetime.now().month

        # Thử import model CongNo
        try:
            from debts.models import CongNo

            # Query công nợ
            debt_query = CongNo.objects.all()
            if selected_month:
                debt_query = debt_query.filter(ngay_tao__month=selected_month)

            # Tính tổng công nợ (dựa trên trường phù hợp)
            total_debt = 0
            total_paid = 0

            for cong_no in debt_query:
                # Giả sử model có trường 'so_tien' và 'con_no'
                if hasattr(cong_no, 'con_no') and cong_no.con_no > 0:
                    total_debt += cong_no.con_no
                if hasattr(cong_no, 'so_tien') and hasattr(cong_no, 'con_no'):
                    total_paid += (cong_no.so_tien - cong_no.con_no)

            # Đếm NCC có công nợ
            total_suppliers_with_debt = debt_query.filter(con_no__gt=0).values('nha_cung_cap').distinct().count()

        except ImportError:
            # Fallback nếu không có model CongNo
            total_debt = 0
            total_paid = 0
            total_suppliers_with_debt = 0

    except Exception as e:
        print(f"Lỗi tính công nợ: {e}")
        total_debt = 0
        total_paid = 0
        total_suppliers_with_debt = 0


    # --- 8. Thống kê tháng hiện tại ---
    current_month = datetime.now().month
    current_year = datetime.now().year

    imports_this_month = NhapKho.objects.filter(
        ngay_tao__month=current_month,
        ngay_tao__year=current_year
    ).count()

    exports_this_month = XuatKho.objects.filter(
        ngay_tao__month=current_month,
        ngay_tao__year=current_year
    ).count()

    # --- 9. Gửi dữ liệu sang template ---
    context = {
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'total_imports': total_imports,
        'total_exports': total_exports,
        'total_inventory': total_inventory,
        'inventory_value': inventory_value,
        'top_products': list(top_products),
        'low_stock': list(low_stock),
        'labels': labels,
        'import_data': import_data,
        'export_data': export_data,
        'imports_this_month': imports_this_month,
        'exports_this_month': exports_this_month,
        'current_year': current_year,

        # Thông tin công nợ mới
        'total_debt': total_debt,
        'total_paid': total_paid,
        'total_suppliers_with_debt': total_suppliers_with_debt,
        'selected_month': selected_month,
    }

    return render(request, 'dashboard.html', context)