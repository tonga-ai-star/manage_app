from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import KiemKe, ChiTietKiemKe
from .models import Kho, TonKho
from products.models import SanPham, DanhMucSanPham, DonViTinh
from .models import NhapKho, ChiTietNhapKho, XuatKho, ChiTietXuatKho
from .forms import NhapKhoForm, ChiTietNhapKhoFormSet, XuatKhoForm, ChiTietXuatKhoFormSet
from .services import QuanLyTonKho
from django.db import transaction
from partners.models import NhaCungCap
from datetime import datetime, timedelta
from debt.models import CongNo
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.db import OperationalError
import json

def danh_sach_nhap(request):
    phieu_nhap = NhapKho.objects.select_related('nha_cung_cap', 'nguoi_lap').order_by('-ngay_nhap')
    context = {'phieu_nhap': phieu_nhap}
    return render(request, 'inventory/nhapkho_list.html', {'phieu_nhap': phieu_nhap})


def generate_ma_ncc():
    """Sinh mã NCC tự động"""
    last = NhaCungCap.objects.order_by('-id').first()
    seq = (last.id + 1) if last else 1
    return f"NCC-{seq:04d}"


@login_required
def nhap_kho_create(request):
    """Tạo phiếu nhập kho với hỗ trợ NCC mới và cập nhật tồn kho"""
    kho_list = Kho.objects.filter(trang_thai='dang_hoat_dong')

    if request.method == 'POST':
        kho_id = request.POST.get('kho_id')
        nha_cung_cap_id = request.POST.get('nha_cung_cap_id')
        nha_cung_cap_moi = request.POST.get('nha_cung_cap_moi', '').strip()
        ghi_chu = request.POST.get('ghi_chu', '').strip()  # Lấy ghi chú từ POST

        try:
            with transaction.atomic():
                # --- 1️⃣ Xử lý nhà cung cấp ---
                if nha_cung_cap_id:
                    nha_cung_cap = get_object_or_404(NhaCungCap, id=nha_cung_cap_id)
                elif nha_cung_cap_moi:
                    nha_cung_cap, _ = NhaCungCap.objects.get_or_create(
                        ten_nha_cung_cap=nha_cung_cap_moi,
                        defaults={'ma_nha_cung_cap': generate_ma_ncc()}
                    )
                else:
                    messages.error(request, "Vui lòng chọn hoặc nhập Nhà cung cấp.")
                    return redirect('inventory:nhap_kho_create')

                # --- 2️⃣ Xử lý kho ---
                if kho_id:
                    try:
                        kho_id = int(kho_id)
                        kho = get_object_or_404(Kho, id=kho_id)
                    except (ValueError, TypeError):
                        messages.error(request, "Kho không hợp lệ!")
                        return redirect('inventory:nhap_kho_create')
                else:
                    messages.error(request, "Vui lòng chọn kho!")
                    return redirect('inventory:nhap_kho_create')
                # Hoặc kho mặc định

                # --- 3️⃣ Tạo phiếu nhập ---
                nhapkho = NhapKho.objects.create(
                    nha_cung_cap=nha_cung_cap,
                    nguoi_lap=request.user,
                    kho=kho,
                    ghi_chu=ghi_chu,
                    ngay_nhap=timezone.now()
                )

                # --- 4️⃣ Lưu chi tiết sản phẩm ---
                ten_san_pham_list = request.POST.getlist('ten_san_pham')
                so_luong_list = request.POST.getlist('so_luong')
                don_gia_list = request.POST.getlist('don_gia')

                tong_tien = Decimal('0')
                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    try:
                        sp = SanPham.objects.get(ten_san_pham=ten_sp)
                        sl = int(so_luong_list[i])
                        dg = Decimal(don_gia_list[i])
                    except (ValueError, IndexError, SanPham.DoesNotExist):
                        continue

                    if sl <= 0 or dg <= 0:
                        continue

                    # Tạo chi tiết nhập
                    ChiTietNhapKho.objects.create(
                        phieu_nhap=nhapkho,
                        san_pham=sp,
                        so_luong=sl,
                        don_gia=dg
                    )

                    # Cập nhật tồn kho
                    ton, created = TonKho.objects.get_or_create(kho=kho, san_pham=sp)
                    ton.so_luong_ton += sl
                    ton.so_luong_kha_dung += sl
                    ton.save()

                    tong_tien += sl * dg

                nhapkho.tong_tien = tong_tien
                nhapkho.save()

                # Tạo công nợ tự động
                tao_cong_no_tu_dong(nhapkho)

                messages.success(request, f"Tạo phiếu nhập {nhapkho.ma_phieu} thành công!")
                return redirect('inventory:nhapkho_list')

        except Exception as e:
            messages.error(request, f"Lỗi khi nhập kho: {e}")

    # GET request
    context = {
        'form': NhapKhoForm(user=request.user),
        'san_pham_list': SanPham.objects.filter(trang_thai=True),
        'nha_cung_cap_list': NhaCungCap.objects.all(),
        'danh_muc_list': DanhMucSanPham.objects.all(),
        'don_vi_tinh_list': DonViTinh.objects.all(),
        'kho_list': kho_list,
    }
    return render(request, 'inventory/nhapkho_form.html', context)


def nhap_kho_detail(request, pk):
    phieu_nhap = get_object_or_404(NhapKho, pk=pk)
    chi_tiet_list = phieu_nhap.chi_tiet_nhap.all()
    return render(request, 'inventory/nhapkho_detail.html', {'phieu_nhap': phieu_nhap, 'chi_tiet_list': chi_tiet_list})


def tao_cong_no_tu_dong(nhapkho):
    from datetime import datetime, timedelta
    from debt.models import CongNo
    han_thanh_toan = datetime.now() + timedelta(days=30)
    CongNo.objects.create(
        nha_cung_cap=nhapkho.nha_cung_cap,
        phieu_nhap=nhapkho,
        loai_cong_no='nhap_hang',
        so_tien=nhapkho.tong_tien,
        so_tien_con_lai=nhapkho.tong_tien,
        han_thanh_toan=han_thanh_toan.date(),
        ghi_chu=f"Công nợ từ phiếu nhập {nhapkho.ma_phieu}"
    )
def xoa_phieu_nhap(request, pk):
    phieu = get_object_or_404(NhapKho, pk=pk)
    if request.method == 'POST':
        phieu.delete()
        return redirect('inventory:nhapkho_list')  # sửa tên url theo project của bạn
    return render(request, 'inventory/xoa_phieu_nhap.html', {'phieu': phieu})


@login_required
def danh_sach_xuat(request):
    xuatkho_list = XuatKho.objects.all().order_by('-ngay_xuat')
    context = {'xuatkho_list': xuatkho_list}
    return render(request, 'inventory/xuatkho_list.html', context)

@login_required
def xuat_kho_create(request):
    kho_list = Kho.objects.filter(trang_thai='dang_hoat_dong')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                kho_xuat_id = request.POST.get('kho_xuat')
                kho_nhan_id = request.POST.get('kho_nhan')
                ghi_chu = request.POST.get('ghi_chu', '').strip()

                if not kho_xuat_id or not kho_nhan_id:
                    messages.error(request, "Vui lòng chọn cả kho xuất và kho nhận!")
                    return redirect('inventory:xuatkho_form')

                kho_xuat = get_object_or_404(Kho, id=kho_xuat_id)
                kho_nhan = get_object_or_404(Kho, id=kho_nhan_id)

                if kho_xuat == kho_nhan:
                    messages.error(request, "Kho xuất và kho nhận không được giống nhau!")
                    return redirect('inventory:xuatkho_form')

                # --- Lấy danh sách sản phẩm và số lượng ---
                ten_san_pham_list = request.POST.getlist('ten_san_pham')
                so_luong_list = request.POST.getlist('so_luong')
                don_gia_list = request.POST.getlist('don_gia')

                # --- Bước 1: Kiểm tra tồn kho trước ---
                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    try:
                        sp = SanPham.objects.get(ten_san_pham=ten_sp)
                        sl = int(so_luong_list[i])
                    except (ValueError, IndexError, SanPham.DoesNotExist):
                        continue

                    ton = QuanLyTonKho.kiem_tra_ton_kho(kho_xuat, sp)
                    if ton['so_luong_kha_dung'] < sl:
                        messages.error(request, f"Sản phẩm {sp.ten_san_pham} không đủ tồn kho (còn {ton['so_luong_kha_dung']})!")
                        return redirect('inventory:xuatkho_form')

                # --- Bước 2: Tạo phiếu xuất ---
                xuatkho = XuatKho.objects.create(
                    nguoi_lap=request.user,
                    kho=kho_xuat,
                    kho_nhan=kho_nhan,
                    ghi_chu=ghi_chu,
                    ngay_xuat=timezone.now()
                )
                # Sinh mã phiếu
                last = XuatKho.objects.order_by('-id').first()
                seq = (last.id + 1) if last else 1
                xuatkho.ma_phieu = f"XKNB-{seq:04d}"
                xuatkho.save()

                # --- Bước 3: Lưu chi tiết và cập nhật tồn kho ---
                tong_tien = Decimal('0')
                for i, ten_sp in enumerate(ten_san_pham_list):
                    if not ten_sp.strip():
                        continue
                    sp = SanPham.objects.get(ten_san_pham=ten_sp)
                    sl = int(so_luong_list[i])
                    dg = Decimal(don_gia_list[i])

                    # Tạo chi tiết xuất
                    ChiTietXuatKho.objects.create(
                        phieu_xuat=xuatkho,
                        san_pham=sp,
                        so_luong=sl,
                        don_gia=dg
                    )

                    # Trừ kho xuất
                    QuanLyTonKho.xuat_hang(kho_xuat, sp, sl)
                    # Cộng kho nhận
                    ton_nhan, created = TonKho.objects.get_or_create(kho=kho_nhan, san_pham=sp)
                    ton_nhan.so_luong_ton += sl
                    ton_nhan.so_luong_kha_dung += sl
                    ton_nhan.save()

                    tong_tien += sl * dg

                xuatkho.tong_tien = tong_tien
                xuatkho.save()

                messages.success(request, f"Tạo phiếu xuất nội bộ {xuatkho.ma_phieu} thành công!")
                return redirect('inventory:xuatkho_list')

        except Exception as e:
            messages.error(request, f"Lỗi khi tạo phiếu xuất: {e}")

    context = {
        'san_pham_list': SanPham.objects.filter(trang_thai=True),
        'danh_muc_list': DanhMucSanPham.objects.all(),
        'don_vi_tinh_list': DonViTinh.objects.all(),
        'kho_list': kho_list,
    }
    return render(request, 'inventory/xuatkho_form.html', context)


def xuat_kho_detail(request, pk):
    phieu_xuat = get_object_or_404(XuatKho, pk=pk)
    chi_tiet_list = phieu_xuat.chi_tiet_xuat.all()
    return render(request, 'inventory/xuatkho_detail.html', {'phieu_xuat': phieu_xuat, 'chi_tiet_list': chi_tiet_list})
def xoa_phieu_xuat(request, pk):
    phieu = get_object_or_404(XuatKho, pk=pk)
    if request.method == 'POST':
        phieu.delete()
        messages.success(request, f"Phiếu xuất {phieu.ma_phieu} đã được xóa!")
        return redirect('inventory:xuatkho_list')
    return render(request, 'inventory/xoa_phieu_xuat.html', {'phieu': phieu})

# ======================
# 📋 KIỂM KÊ
# ======================

@login_required
def danh_sach_kiem_ke(request):
    try:
        danh_sach = KiemKe.objects.all().order_by('-ngay_tao')
    except OperationalError:
        danh_sach = []
        messages.error(request, 'Có lỗi database. Vui lòng chạy migrations.')

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
    try:
        # Đảm bảo id là số nguyên
        kiem_ke_id = int(id)
        kiem_ke = get_object_or_404(KiemKe, id=kiem_ke_id)
    except (ValueError, TypeError):
        # Nếu không phải số, thử tìm bằng mã kiểm kê
        try:
            kiem_ke = get_object_or_404(KiemKe, ma_kiem_ke=id)
        except:
            messages.error(request, 'Không tìm thấy đợt kiểm kê')
            return redirect('inventory:danh_sach_kiem_ke')

    # Kiểm tra xem kho có phải là instance của Kho không
    if not isinstance(kiem_ke.kho, Kho):
        messages.error(request, 'Dữ liệu kho không hợp lệ')
        return redirect('inventory:danh_sach_kiem_ke')

    # Lấy danh sách sản phẩm
    san_phams = SanPham.objects.all()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                for san_pham in san_phams:
                    so_luong_thuc_te_key = f'so_luong_{san_pham.id}'
                    so_luong_thuc_te = request.POST.get(so_luong_thuc_te_key)

                    if so_luong_thuc_te and so_luong_thuc_te.strip():
                        # Kiểm tra tồn kho
                        ton_kho_info = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)
                        so_luong_he_thong = ton_kho_info['so_luong_ton']
                        so_luong_thuc_te_int = int(so_luong_thuc_te)

                        # Tạo hoặc cập nhật chi tiết kiểm kê
                        chi_tiet, created = ChiTietKiemKe.objects.get_or_create(
                            kiem_ke=kiem_ke,
                            san_pham=san_pham,
                            defaults={
                                'so_luong_he_thong': so_luong_he_thong,
                                'so_luong_thuc_te': so_luong_thuc_te_int
                            }
                        )

                        if not created:
                            chi_tiet.so_luong_he_thong = so_luong_he_thong
                            chi_tiet.so_luong_thuc_te = so_luong_thuc_te_int
                            chi_tiet.save()

                kiem_ke.trang_thai = 'hoan_thanh'
                kiem_ke.save()

                messages.success(request, 'Cập nhật kiểm kê thành công!')
                return redirect('inventory:danh_sach_kiem_ke')

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    # Chuẩn bị dữ liệu cho template
    chi_tiet_kiem_ke_list = []
    for san_pham in san_phams:
        # Kiểm tra tồn kho
        try:
            ton_kho_info = QuanLyTonKho.kiem_tra_ton_kho(kiem_ke.kho, san_pham)
            so_luong_he_thong = ton_kho_info['so_luong_ton']
        except:
            so_luong_he_thong = 0

        # Lấy chi tiết kiểm kê hiện có
        chi_tiet_existing = ChiTietKiemKe.objects.filter(
            kiem_ke=kiem_ke,
            san_pham=san_pham
        ).first()

        chi_tiet_kiem_ke_list.append({
            'san_pham': san_pham,
            'so_luong_he_thong': so_luong_he_thong,
            'so_luong_thuc_te': chi_tiet_existing.so_luong_thuc_te if chi_tiet_existing else so_luong_he_thong,
            'chenh_lech': chi_tiet_existing.chenh_lech if chi_tiet_existing else 0,
            'ghi_chu': chi_tiet_existing.ghi_chu if chi_tiet_existing else ''
        })

    context = {
        'kiem_ke': kiem_ke,
        'chi_tiet_kiem_ke_list': chi_tiet_kiem_ke_list
    }
    return render(request, 'inventory/chi_tiet_kiem_ke.html', context)
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
def chi_tiet_ton_kho(request, kho_id=None):
    # Lấy danh sách kho và sản phẩm để filter
    danh_sach_kho = Kho.objects.filter(trang_thai='dang_hoat_dong')
    danh_sach_san_pham = SanPham.objects.all()

    # Lọc theo GET params hoặc theo kho_id từ URL
    san_pham_id = request.GET.get('san_pham')

    ton_kho = TonKho.objects.all()
    if kho_id:
        ton_kho = ton_kho.filter(kho_id=kho_id)
    if san_pham_id:
        ton_kho = ton_kho.filter(san_pham_id=san_pham_id)

    context = {
        'danh_sach_kho': danh_sach_kho,
        'danh_sach_san_pham': danh_sach_san_pham,
        'ton_kho': ton_kho,
        'selected_kho': kho_id,
        'selected_san_pham': san_pham_id,
    }
    return render(request, 'inventory/chi_tiet_ton_kho.html', context)


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