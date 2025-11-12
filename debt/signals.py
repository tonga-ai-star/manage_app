from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from inventory.models import NhapKho
from .models import CongNo


@receiver(post_save, sender=NhapKho)
def tao_cong_no_tu_nhap_kho(sender, instance, created, **kwargs):
    if created and instance.trang_thai == 'hoan_tat':
        try:
            # Tạo mã công nợ tự động
            ma_cong_no = f"CN{instance.id:04d}"

            # Lấy thông tin hàng hóa
            ten_hang_hoa = "Hàng nhập kho"
            if hasattr(instance, 'chitietnhapkho_set') and instance.chitietnhapkho_set.exists():
                items = list(instance.chitietnhapkho_set.all())
                ten_hang_hoa = ", ".join([str(item.hang_hoa) for item in items[:3]])  # Lấy 3 món đầu
                if len(items) > 3:
                    ten_hang_hoa += "..."

            CongNo.objects.create(
                nha_cung_cap=instance.nha_cung_cap,
                phieu_nhap=instance,
                ma_cong_no=ma_cong_no,
                loai_cong_no='phai_tra',
                ten_hang_hoa=ten_hang_hoa[:255],
                so_luong=1,
                don_gia=instance.tong_tien,
                han_thanh_toan=timezone.now().date() + timedelta(days=30)
            )
        except Exception as e:
            print(f"Lỗi khi tạo công nợ từ nhập kho: {e}")