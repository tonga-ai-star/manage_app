from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import KiemKe, ChiTietKiemKe
from .models import Kho, TonKho
from django.contrib import messages
from products.models import SanPham
from .models import NhapKho, ChiTietNhapKho, XuatKho, ChiTietXuatKho
from .forms import NhapKhoForm, ChiTietNhapKhoFormSet, XuatKhoForm, ChiTietXuatKhoFormSet
from .services import QuanLyTonKho
from django.db import transaction
import json


# ======================
# 📦 NHẬP KHO
# ======================
def danh_sach_nhap(request):
    """Danh sách phiếu nhập kho"""
    phieu_nhap_list = NhapKho.objects.select_related('nha_cung_cap', 'nguoi_lap').order_by('-ngay_nhap')
    return render(request, 'inventory/nhapkho_list.html', {'phieu_nhap_list': phieu_nhap_list})


@login_required
def nhap_kho_create(request):
    """Tạo phiếu nhập kho"""
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')
    if request.method == 'POST':
        form = NhapKhoForm(request.POST, user=request.user)
        formset = ChiTietNhapKhoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    nhapkho = form.save(commit=False)
                    nhapkho.nguoi_lap = request.user
                    nhapkho.save()
                    formset.instance = nhapkho
                    formset.save()

                    # Cập nhật tồn kho sau khi nhập
                    for chi_tiet in nhapkho.chi_tiet_nhap.all():
                        QuanLyTonKho.nhap_hang(nhapkho.kho, chi_tiet.san_pham, chi_tiet.so_luong)

                    tao_cong_no_tu_dong(nhapkho)

                    messages.success(request, f'Tạo phiếu nhập kho {nhapkho.ma_phieu} thành công!')
                    return redirect('inventory:danh_sach_nhap')
            except Exception as e:
                messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin nhập!')
    else:
        form = NhapKhoForm(user=request.user)
        formset = ChiTietNhapKhoFormSet()

    context = {'form': form, 'formset': formset, 'title': 'Tạo Phiếu Nhập Kho', 'danh_sach_kho': danh_sach_kho}
    return render(request, 'inventory/nhapkho_form.html', context)


def nhap_kho_detail(request, pk):
    """Chi tiết phiếu nhập kho"""
    phieu_nhap = get_object_or_404(NhapKho, pk=pk)
    chi_tiet_list = phieu_nhap.chi_tiet_nhap.all()
    return render(request, 'inventory/nhapkho_detail.html', {'phieu_nhap': phieu_nhap, 'chi_tiet_list': chi_tiet_list})


def tao_cong_no_tu_dong(nhapkho):
    """Tự động tạo công nợ khi nhập hàng"""
    from datetime import datetime, timedelta
    from debt.models import CongNoNhaCungCap

    han_thanh_toan = datetime.now() + timedelta(days=30)
    CongNoNhaCungCap.objects.create(
        nha_cung_cap=nhapkho.nha_cung_cap,
        phieu_nhap=nhapkho,
        loai_cong_no='nhap_hang',
        so_tien=nhapkho.tong_tien,
        so_tien_con_lai=nhapkho.tong_tien,
        han_thanh_toan=han_thanh_toan.date(),
        ghi_chu=f"Công nợ từ phiếu nhập {nhapkho.ma_phieu}"
    )


# ======================
# 📤 XUẤT KHO
# ======================
def danh_sach_xuat(request):
    """Danh sách phiếu xuất kho"""
    xuatkho_list = XuatKho.objects.select_related('nguoi_lap').order_by('-ngay_xuat')
    return render(request, 'inventory/xuatkho_list.html', {'xuatkho_list': xuatkho_list})


@login_required
def xuat_kho_create(request):
    """Tạo phiếu xuất kho"""
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')

    if request.method == 'POST':
        form = XuatKhoForm(request.POST, user=request.user)
        formset = ChiTietXuatKhoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Kiểm tra tồn kho trước khi tạo phiếu
                    xuatkho = form.save(commit=False)

                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            san_pham = form.cleaned_data.get('san_pham')
                            so_luong = form.cleaned_data.get('so_luong')

                            if san_pham and so_luong:
                                ton_kho = QuanLyTonKho.kiem_tra_ton_kho(xuatkho.kho, san_pham)
                                if ton_kho['so_luong_kha_dung'] < so_luong:
                                    messages.error(
                                        request,
                                        f'Không đủ tồn kho cho {san_pham.ten_san_pham}. '
                                        f'Yêu cầu: {so_luong}, Tồn kho: {ton_kho["so_luong_kha_dung"]}'
                                    )
                                    return render(request, 'inventory/xuatkho_form.html', {
                                        'form': form,
                                        'formset': formset,
                                        'title': 'Tạo Phiếu Xuất Kho',
                                        'danh_sach_kho': danh_sach_kho
                                    })

                    xuatkho.nguoi_lap = request.user
                    xuatkho.save()
                    formset.instance = xuatkho
                    formset.save()

                    # Cập nhật tồn kho sau khi xuất
                    for chi_tiet in xuatkho.chi_tiet_xuat.all():
                        QuanLyTonKho.xuat_hang(xuatkho.kho, chi_tiet.san_pham, chi_tiet.so_luong)

                    messages.success(request, f'Tạo phiếu xuất kho {xuatkho.ma_phieu} thành công!')
                    return redirect('inventory:danh_sach_xuat')

            except Exception as e:
                messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin!')
    else:
        form = XuatKhoForm(user=request.user)
        formset = ChiTietXuatKhoFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Tạo Phiếu Xuất Kho',
        'danh_sach_kho': danh_sach_kho
    }
    return render(request, 'inventory/xuatkho_form.html', context)


def xuat_kho_detail(request, pk):
    """Chi tiết phiếu xuất kho"""
    phieu_xuat = get_object_or_404(XuatKho, pk=pk)
    chi_tiet_list = phieu_xuat.chi_tiet_xuat.all()
    return render(request, 'inventory/xuatkho_detail.html', {'phieu_xuat': phieu_xuat, 'chi_tiet_list': chi_tiet_list})


def get_product_info(request, product_id):
    """API lấy thông tin sản phẩm"""
    try:
        product = SanPham.objects.get(id=product_id)
        return JsonResponse({
            'ten_san_pham': product.ten_san_pham,
            'gia_ban': float(product.gia_ban or 0),
            'gia_von': float(product.gia_von or 0),
            'ton_kho': product.ton_kho,
            'don_vi_tinh': product.don_vi_tinh
        })
    except SanPham.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy sản phẩm'}, status=404)


# ======================
# 📋 KIỂM KÊ
# ======================
@login_required
def danh_sach_kiem_ke(request):
    danh_sach = KiemKe.objects.all().order_by('-ngay_tao')
    return render(request, 'inventory/danh_sach_kiem_ke.html', {
        'danh_sach_kiem_ke': danh_sach
    })


@login_required
def tao_kiem_ke(request):
    if request.method == 'POST':
        try:
            ma_kiem_ke = request.POST.get('ma_kiem_ke')
            ten_dot_kiem_ke = request.POST.get('ten_dot_kiem_ke')
            ngay_kiem_ke = request.POST.get('ngay_kiem_ke')
            kho_id = request.POST.get('kho')
            mo_ta = request.POST.get('mo_ta', '')

            # Kiểm tra mã kiểm kê đã tồn tại chưa
            if KiemKe.objects.filter(ma_kiem_ke=ma_kiem_ke).exists():
                messages.error(request, 'Mã kiểm kê đã tồn tại! Vui lòng chọn mã khác.')
                return render(request, 'inventory/tao_kiem_ke.html')

            kho = get_object_or_404(Kho, id=kho_id)

            kiem_ke = KiemKe(
                ma_kiem_ke=ma_kiem_ke,
                ten_dot_kiem_ke=ten_dot_kiem_ke,
                ngay_kiem_ke=ngay_kiem_ke,
                kho=kho,
                mo_ta=mo_ta,
                nguoi_phu_trach=request.user
            )
            kiem_ke.save()

            messages.success(request, f'Tạo đợt kiểm kê "{ten_dot_kiem_ke}" thành công!')
            return redirect('inventory:chi_tiet_kiem_ke', id=kiem_ke.id)

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'inventory/tao_kiem_ke.html')

    # GET request - hiển thị form
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')
    return render(request, 'inventory/tao_kiem_ke.html', {'danh_sach_kho': danh_sach_kho})


@login_required
def chi_tiet_kiem_ke(request, id):
    kiem_ke = get_object_or_404(KiemKe, id=id)
    san_phams = SanPham.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for san_pham in san_phams:
                    so_luong_thuc_te = request.POST.get(f'so_luong_{san_pham.id}')
                    if so_luong_thuc_te:
                        so_luong_he_thong = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)['so_luong_ton']

                        chi_tiet, created = ChiTietKiemKe.objects.get_or_create(
                            kiem_ke=kiem_ke,
                            san_pham=san_pham,
                            defaults={
                                'so_luong_he_thong': so_luong_he_thong,
                                'so_luong_thuc_te': int(so_luong_thuc_te)
                            }
                        )
                        if not created:
                            chi_tiet.so_luong_he_thong = so_luong_he_thong
                            chi_tiet.so_luong_thuc_te = int(so_luong_thuc_te)
                            chi_tiet.save()

                kiem_ke.trang_thai = 'hoan_thanh'
                kiem_ke.save()

                messages.success(request, 'Cập nhật kiểm kê thành công!')
                return redirect('inventory:danh_sach_kiem_ke')

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    # Lấy tồn kho hiện tại cho từng sản phẩm
    for san_pham in san_phams:
        san_pham.so_luong_ton_hien_tai = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)['so_luong_ton']

    return render(request, 'inventory/chi_tiet_kiem_ke.html', {
        'kiem_ke': kiem_ke,
        'san_phams': san_phams
    })


# ======================
# 🏢 QUẢN LÝ KHO
# ======================
@login_required
def danh_sach_kho(request):
    danh_sach_kho = Kho.objects.all().order_by('ma_kho')
    return render(request, 'inventory/danh_sach_kho.html', {
        'danh_sach_kho': danh_sach_kho
    })


@login_required
def tao_kho(request):
    if request.method == 'POST':
        ma_kho = request.POST.get('ma_kho')
        ten_kho = request.POST.get('ten_kho')
        dia_chi = request.POST.get('dia_chi')
        dien_thoai = request.POST.get('dien_thoai')

        if Kho.objects.filter(ma_kho=ma_kho).exists():
            messages.error(request, 'Mã kho đã tồn tại!')
            return render(request, 'inventory/tao_kho.html')

        kho = Kho(
            ma_kho=ma_kho,
            ten_kho=ten_kho,
            dia_chi=dia_chi,
            dien_thoai=dien_thoai,
            nguoi_quan_ly=request.user
        )
        kho.save()
        messages.success(request, 'Tạo kho thành công!')
        return redirect('inventory:danh_sach_kho')

    return render(request, 'inventory/tao_kho.html')


@login_required
def chi_tiet_ton_kho(request, kho_id):
    kho = get_object_or_404(Kho, id=kho_id)
    ton_kho = TonKho.objects.filter(kho=kho).select_related('san_pham')

    return render(request, 'inventory/chi_tiet_ton_kho.html', {
        'kho': kho,
        'ton_kho': ton_kho
    })


# ======================
# 🔧 API & UTILITIES
# ======================
def kiem_tra_ton_kho_api(request, kho_id, san_pham_id):
    """API kiểm tra tồn kho"""
    try:
        kho = get_object_or_404(Kho, id=kho_id)
        san_pham = get_object_or_404(SanPham, id=san_pham_id)

        ton_kho = QuanLyTonKho.kiem_tra_ton_kho(kho, san_pham)

        return JsonResponse({
            'success': True,
            'so_luong_ton': ton_kho['so_luong_ton'],
            'so_luong_kha_dung': ton_kho['so_luong_kha_dung']
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_danh_sach_kho_api(request):
    """API lấy danh sách kho"""
    try:
        danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong').values('id', 'ma_kho', 'ten_kho')
        return JsonResponse({
            'success': True,
            'danh_sach_kho': list(danh_sach_kho)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })