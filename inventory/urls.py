from django.urls import path
from . import views
app_name = 'inventory'
urlpatterns = [
    path('nhap-kho/', views.danh_sach_nhap, name='danh_sach_nhap'),
    path('nhap-kho/them/', views.nhap_kho_create, name='nhap_kho_create'),
    path('nhap-kho/<int:pk>/', views.nhap_kho_detail, name='nhap_kho_detail'),
    path('xuat-kho/', views.danh_sach_xuat, name='danh_sach_xuat'),
    path('xuat-kho/them/', views.xuat_kho_create, name='xuat_kho_create'),
    path('xuat-kho/<int:pk>/', views.xuat_kho_detail, name='xuat_kho_detail'),
    path('', views.danh_sach_kiem_ke, name='danh_sach_kiem_ke'),
    path('tao-kiem-ke/', views.tao_kiem_ke, name='tao_kiem_ke'),
    path('chi-tiet-kiem-ke/<int:id>/', views.chi_tiet_kiem_ke, name='chi_tiet_kiem_ke'),
]