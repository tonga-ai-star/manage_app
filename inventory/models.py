from django.db import models
from django.conf import settings  # THÊM DÒNG NÀY
from django.core.validators import MinValueValidator
from products.models import SanPham
from partners.models import NhaCungCap, KhachHang
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User




class NhapKho(models.Model):
    ma_phieu = models.CharField(max_length=50, unique=True)
    ngay_nhap = models.DateTimeField(auto_now_add=True)
    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    nguoi_lap = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE)  # SỬA THÀNH settings.AUTH_USER_MODEL
    tong_tien = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ma_phieu

    def save(self, *args, **kwargs):
        if not self.ma_phieu:
            last_phieu = NhapKho.objects.order_by('-id').first()
            if last_phieu:
                last_number = int(last_phieu.ma_phieu.split('-')[-1])
                self.ma_phieu = f'NK-{last_number + 1:04d}'
            else:
                self.ma_phieu = 'NK-0001'
        super().save(*args, **kwargs)
        self.update_tong_tien()

    def update_tong_tien(self):
        """Cập nhật tổng tiền phiếu nhập"""
        total = self.chi_tiet_nhap.aggregate(
            total=Sum('thanh_tien')
        )['total'] or Decimal('0')

        self.tong_tien = total
        # Sử dụng update để tránh recursive save
        NhapKho.objects.filter(id=self.id).update(tong_tien=total)

    class Meta:
        verbose_name = "Phiếu nhập kho"
        verbose_name_plural = "Phiếu nhập kho"
        ordering=['-ngay_nhap']


class ChiTietNhapKho(models.Model):
    phieu_nhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE, related_name='chi_tiet_nhap')
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(validators=[MinValueValidator(1)])
    don_gia = models.DecimalField(max_digits=15, decimal_places=2)
    thanh_tien = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.thanh_tien = self.so_luong * self.don_gia
        super().save(*args, **kwargs)

        # Cập nhật tồn kho sản phẩm
        self.thanh_tien = self.so_luong * self.don_gia

        # Kiểm tra xem là tạo mới hay cập nhật
        is_new = self.pk is None

        super().save(*args, **kwargs)

        # Cập nhật tổng tiền phiếu nhập
        self.phieu_nhap.update_tong_tien()

        # Cập nhật tồn kho sản phẩm
        if is_new:
            self.san_pham.ton_kho += self.so_luong
            self.san_pham.save()

    def delete(self, *args, **kwargs):
        # Lưu thông tin trước khi xóa
        phieu_nhap = self.phieu_nhap
        san_pham = self.san_pham
        so_luong = self.so_luong

        super().delete(*args, **kwargs)

        # Cập nhật tổng tiền phiếu nhập
        phieu_nhap.update_tong_tien()

        # Trừ tồn kho sản phẩm
        san_pham.ton_kho -= so_luong
        san_pham.save()

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.so_luong}"
    class Meta:
        verbose_name = "Chi tiết nhập kho"
        verbose_name_plural = "Chi tiết nhập kho"


class XuatKho(models.Model):
    ma_phieu = models.CharField(max_length=50, unique=True)
    ngay_xuat = models.DateTimeField(auto_now_add=True)
    khach_hang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    nguoi_lap = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE)  # SỬA THÀNH settings.AUTH_USER_MODEL
    tong_tien = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ma_phieu

    def save(self, *args, **kwargs):
        if not self.ma_phieu:
            last_phieu = XuatKho.objects.order_by('-id').first()
            if last_phieu:
                last_number = int(last_phieu.ma_phieu.split('-')[-1])
                self.ma_phieu = f'XK-{last_number + 1:04d}'
            else:
                self.ma_phieu = 'XK-0001'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Phiếu xuất kho"
        verbose_name_plural = "Phiếu xuất kho"


class ChiTietXuatKho(models.Model):
    phieu_xuat = models.ForeignKey(XuatKho, on_delete=models.CASCADE, related_name='chi_tiet_xuat')
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    so_luong = models.IntegerField(validators=[MinValueValidator(1)])
    don_gia = models.DecimalField(max_digits=15, decimal_places=2)
    thanh_tien = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.thanh_tien = self.so_luong * self.don_gia
        super().save(*args, **kwargs)

        # Trừ tồn kho sản phẩm
        if self.san_pham.ton_kho >= self.so_luong:
            self.san_pham.ton_kho -= self.so_luong
            self.san_pham.save()

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.so_luong}"

    class Meta:
        verbose_name = "Chi tiết xuất kho"
        verbose_name_plural = "Chi tiết xuất kho"


from django.db import models
from django.conf import settings  # Thêm dòng này
from products.models import SanPham  # Import model sản phẩm từ app products


class KiemKe(models.Model):
    TRANG_THAI_CHON = [
        ('cho', 'Chờ'),
        ('dang_kiem_ke', 'Đang kiểm kê'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy'),
    ]

    ma_kiem_ke = models.CharField(max_length=50, unique=True, verbose_name="Mã kiểm kê")
    ten_dot_kiem_ke = models.CharField(max_length=200, verbose_name="Tên đợt kiểm kê")
    ngay_kiem_ke = models.DateTimeField(verbose_name="Ngày kiểm kê")
    kho = models.CharField(max_length=100, verbose_name="Kho kiểm kê")
    nguoi_phu_trach = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Sửa thành này
        on_delete=models.CASCADE,
        verbose_name="Người phụ trách"
    )
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_CHON, default='cho', verbose_name="Trạng thái")
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả")
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kiểm kê"
        verbose_name_plural = "Kiểm kê"

    def __str__(self):
        return f"{self.ma_kiem_ke} - {self.ten_dot_kiem_ke}"


class ChiTietKiemKe(models.Model):
    kiem_ke = models.ForeignKey(KiemKe, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name="Đợt kiểm kê")
    san_pham = models.ForeignKey(SanPham, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    so_luong_he_thong = models.IntegerField(verbose_name="Số lượng hệ thống")
    so_luong_thuc_te = models.IntegerField(verbose_name="Số lượng thực tế")
    chenh_lech = models.IntegerField(default=0, verbose_name="Chênh lệch")
    ghi_chu = models.TextField(blank=True, verbose_name="Ghi chú")

    class Meta:
        verbose_name = "Chi tiết kiểm kê"
        verbose_name_plural = "Chi tiết kiểm kê"

    def save(self, *args, **kwargs):
        self.chenh_lech = self.so_luong_thuc_te - self.so_luong_he_thong
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.chenh_lech}"