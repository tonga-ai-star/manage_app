
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
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    # DÙNG DỮ LIỆU GIẢ - KHÔNG TRUY VẤN DATABASE
    context = {
        'total_products': 156,
        'total_imports': 23,
        'total_exports': 45,
        'total_suppliers': 8,
        'total_customers': 12,
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