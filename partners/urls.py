from django.urls import path
from . import views

urlpatterns = [
    path('nha-cung-cap/', views.supplier_list, name='supplier_list'),
    path('nha-cung-cap/them/', views.supplier_create, name='supplier_create'),
    path('khach-hang/', views.customer_list, name='customer_list'),
    path('khach-hang/them/', views.customer_create, name='customer_create'),
]