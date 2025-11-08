from django.urls import path
from . import views

urlpatterns = [
    path('nhap-kho/', views.danh_sach_nhap, name='danh_sach_nhap'),
    path('nhap-kho/them/', views.nhap_kho_create, name='nhap_kho_create'),
    path('nhap-kho/<int:pk>/', views.nhap_kho_detail, name='nhap_kho_detail'),
    path('xuat-kho/', views.danh_sach_xuat, name='danh_sach_xuat'),
    path('xuat-kho/them/', views.xuat_kho_create, name='xuat_kho_create'),
    path('xuat-kho/<int:pk>/', views.xuat_kho_detail, name='xuat_kho_detail'),
]