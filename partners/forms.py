from django import forms
from .models import NhaCungCap, KhachHang

class NhaCungCapForm(forms.ModelForm):
    class Meta:
        model = NhaCungCap
        fields = ['ma_nha_cung_cap', 'ten_nha_cung_cap', 'dia_chi', 'dien_thoai', 'email', 'ghi_chu']
        widgets = {
            'ma_nha_cung_cap': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mã nhà cung cấp'}),
            'ten_nha_cung_cap': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên nhà cung cấp'}),
            'dia_chi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Địa chỉ'}),
            'dien_thoai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ghi chú'}),
        }

class KhachHangForm(forms.ModelForm):
    class Meta:
        model = KhachHang
        fields = ['ma_khach_hang', 'ten_khach_hang', 'dia_chi', 'dien_thoai', 'email', 'ghi_chu']
        widgets = {
            'ma_khach_hang': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mã khách hàng'}),
            'ten_khach_hang': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên khách hàng'}),
            'dia_chi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Địa chỉ'}),
            'dien_thoai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'ghi_chu': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ghi chú'}),
        }