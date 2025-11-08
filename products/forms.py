from django import forms
from .models import SanPham

class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = '__all__'
        widgets = {
            'ma_san_pham': forms.TextInput(attrs={'class': 'form-control'}),
            'ten_san_pham': forms.TextInput(attrs={'class': 'form-control'}),
            'danh_muc': forms.Select(attrs={'class': 'form-select'}),
            'don_vi_tinh': forms.Select(attrs={'class': 'form-select'}),
            'gia_nhap': forms.NumberInput(attrs={'class': 'form-control'}),
            'gia_ban': forms.NumberInput(attrs={'class': 'form-control'}),
            'ton_kho': forms.NumberInput(attrs={'class': 'form-control'}),
            'trang_thai': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
