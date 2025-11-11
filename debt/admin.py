from django.contrib import admin
from .models import CongNoNhaCungCap, LichSuThanhToan


class LichSuThanhToanInline(admin.TabularInline):
    model = LichSuThanhToan
    extra = 1
    fields = ['so_tien_thanh_toan', 'ngay_thanh_toan', 'ghi_chu']


@admin.register(CongNoNhaCungCap)
class CongNoNhaCungCapAdmin(admin.ModelAdmin):
    list_display = [
        'nha_cung_cap',
        'so_tien',
        'so_tien_con_lai',
        'han_thanh_toan',
        'trang_thai'
    ]

    list_filter = [
        'trang_thai',
        'loai_cong_no'
    ]

    search_fields = [
        'nha_cung_cap__ten',
        'ghi_chu'
    ]

    readonly_fields = ['ngay_tao', 'ngay_cap_nhat']

    inlines = [LichSuThanhToanInline]

    fieldsets = (
        ('Thông tin chung', {
            'fields': (
                'nha_cung_cap',
                'phieu_nhap',
                'loai_cong_no'
            )
        }),
        ('Số tiền', {
            'fields': (
                'so_tien',
                'so_tien_con_lai'
            )
        }),
        ('Thời hạn & Trạng thái', {
            'fields': (
                'han_thanh_toan',
                'trang_thai'
            )
        }),
        ('Ghi chú', {
            'fields': ('ghi_chu',)
        })
    )


@admin.register(LichSuThanhToan)
class LichSuThanhToanAdmin(admin.ModelAdmin):
    list_display = [
        'cong_no',
        'so_tien_thanh_toan',
        'ngay_thanh_toan'
    ]

    list_filter = ['ngay_thanh_toan']
    search_fields = ['cong_no__nha_cung_cap__ten']