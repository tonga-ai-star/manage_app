from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from partners.models import NhaCungCap
from inventory.models import NhapKho
from datetime import date


class CongNoNhaCungCap(models.Model):
    LOAI_CONG_NO = [
        ('nhap_hang', 'Nợ nhập hàng'),
        ('thanh_toan', 'Thanh toán'),
    ]

    TRANG_THAI = [
        ('dang_no', 'Đang nợ'),
        ('thanh_toan_mot_phan', 'Thanh toán một phần'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('qua_han', 'Quá hạn'),
    ]

    nha_cung_cap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    phieu_nhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE, null=True, blank=True)
    loai_cong_no = models.CharField(max_length=20, choices=LOAI_CONG_NO)
    so_tien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    so_tien_con_lai = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    han_thanh_toan = models.DateField()
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='dang_no')
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Tự động cập nhật trạng thái
        if self.so_tien_con_lai <= 0:
            self.trang_thai = 'da_thanh_toan'
        elif self.so_tien_con_lai < self.so_tien:
            self.trang_thai = 'thanh_toan_mot_phan'
        elif date.today() > self.han_thanh_toan:
            self.trang_thai = 'qua_han'
        else:
            self.trang_thai = 'dang_no'

        super().save(*args, **kwargs)

    def thanh_toan(self, so_tien_thanh_toan, ngay_thanh_toan=None):
        """Thực hiện thanh toán công nợ"""
        if so_tien_thanh_toan <= 0:
            raise ValueError("Số tiền thanh toán phải lớn hơn 0")

        if so_tien_thanh_toan > self.so_tien_con_lai:
            raise ValueError("Số tiền thanh toán không được vượt quá số nợ còn lại")

        self.so_tien_con_lai -= so_tien_thanh_toan
        self.save()

        # Tạo lịch sử thanh toán
        LichSuThanhToan.objects.create(
            cong_no=self,
            so_tien_thanh_toan=so_tien_thanh_toan,
            ngay_thanh_toan=ngay_thanh_toan or date.today(),
            ghi_chu=f"Thanh toán cho công nợ {self.id}"
        )

    @property
    def qua_han(self):
        return date.today() > self.han_thanh_toan and self.so_tien_con_lai > 0

    @property
    def so_ngay_qua_han(self):
        if self.qua_han:
            return (date.today() - self.han_thanh_toan).days
        return 0

    def __str__(self):
        return f"{self.nha_cung_cap.ten} - {self.so_tien:,.0f} VND"

    class Meta:
        verbose_name = "Công nợ nhà cung cấp"
        verbose_name_plural = "Công nợ nhà cung cấp"
        ordering = ['-han_thanh_toan']


class LichSuThanhToan(models.Model):
    cong_no = models.ForeignKey(CongNoNhaCungCap, on_delete=models.CASCADE, related_name='lich_su_thanh_toan')
    so_tien_thanh_toan = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    ngay_thanh_toan = models.DateField()
    ghi_chu = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Thanh toán {self.so_tien_thanh_toan:,.0f} VND - {self.ngay_thanh_toan}"

    class Meta:
        verbose_name = "Lịch sử thanh toán"
        verbose_name_plural = "Lịch sử thanh toán"
        ordering = ['-ngay_thanh_toan']
