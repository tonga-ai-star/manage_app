from django.urls import path
from . import views

app_name = 'debt'

urlpatterns = [
    path('', views.CongNoListView.as_view(), name='congno_list'),
    path('tao-moi/', views.congno_create, name='congno_create'),
    path('<int:pk>/', views.CongNoDetailView.as_view(), name='congno_detail'),
    path('<int:pk>/cap-nhat/', views.CongNoUpdateView.as_view(), name='congno_update'),
    path('<int:pk>/thanh-toan/', views.thanh_toan_cong_no, name='thanh_toan'),
    path('<int:pk>/xoa/', views.congno_delete, name='congno_delete'),
    path('bao-cao/', views.bao_cao_cong_no, name='bao_cao'),
    path('api/phieu-nhap/<int:nha_cung_cap_id>/', views.get_phieu_nhap_theo_nha_cung_cap, name='get_phieu_nhap'),
]