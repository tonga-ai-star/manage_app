from django.contrib import admin
from .models import NhapKho, ChiTietNhapKho, XuatKho, ChiTietXuatKho
from .models import KiemKe, ChiTietKiemKe
class ChiTietNhapKhoInline(admin.TabularInline):
    model = ChiTietNhapKho
    extra = 1
    fields = ['san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    readonly_fields = ['thanh_tien']

@admin.register(NhapKho)
class NhapKhoAdmin(admin.ModelAdmin):
    list_display = ['ma_phieu', 'ngay_nhap', 'nha_cung_cap', 'tong_tien', 'nguoi_lap']
    list_filter = ['ngay_nhap', 'nha_cung_cap']
    search_fields = ['ma_phieu', 'nha_cung_cap__ten_nha_cung_cap']
    inlines = [ChiTietNhapKhoInline]

class ChiTietXuatKhoInline(admin.TabularInline):
    model = ChiTietXuatKho
    extra = 1
    fields = ['san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    readonly_fields = ['thanh_tien']

@admin.register(XuatKho)
class XuatKhoAdmin(admin.ModelAdmin):
    list_display = ['ma_phieu', 'ngay_xuat', 'khach_hang', 'tong_tien', 'nguoi_lap']
    list_filter = ['ngay_xuat', 'khach_hang']
    search_fields = ['ma_phieu', 'khach_hang__ten_khach_hang']
    inlines = [ChiTietXuatKhoInline]

@admin.register(ChiTietNhapKho)
class ChiTietNhapKhoAdmin(admin.ModelAdmin):
    list_display = ['phieu_nhap', 'san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    list_filter = ['phieu_nhap', 'san_pham']

@admin.register(ChiTietXuatKho)
class ChiTietXuatKhoAdmin(admin.ModelAdmin):
    list_display = ['phieu_xuat', 'san_pham', 'so_luong', 'don_gia', 'thanh_tien']
    list_filter = ['phieu_xuat', 'san_pham']


class ChiTietKiemKeInline(admin.TabularInline):
    model = ChiTietKiemKe
    extra = 1

@admin.register(KiemKe)
class KiemKeAdmin(admin.ModelAdmin):
    list_display = ['ma_kiem_ke', 'ten_dot_kiem_ke', 'kho', 'ngay_kiem_ke', 'trang_thai', 'nguoi_phu_trach']
    list_filter = ['trang_thai', 'kho', 'ngay_kiem_ke']
    search_fields = ['ma_kiem_ke', 'ten_dot_kiem_ke']
    inlines = [ChiTietKiemKeInline]

@admin.register(ChiTietKiemKe)
class ChiTietKiemKeAdmin(admin.ModelAdmin):
    list_display = ['kiem_ke', 'san_pham', 'so_luong_he_thong', 'so_luong_thuc_te', 'chenh_lech']
    list_filter = ['kiem_ke']