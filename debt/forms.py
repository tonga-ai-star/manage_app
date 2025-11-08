from django import forms
from .models import CongNoNhaCungCap, LichSuThanhToan
from partners.models import NhaCungCap
from inventory.models import NhapKho
from datetime import date, timedelta
import re


class CongNoNhaCungCapForm(forms.ModelForm):
    class Meta:
        model = CongNoNhaCungCap
        fields = ['nha_cung_cap', 'phieu_nhap', 'loai_cong_no', 'so_tien', 'han_thanh_toan', 'ghi_chu']
        widgets = {
            'nha_cung_cap': forms.Select(attrs={
                'class': 'form-control select2',
                'id': 'nha-cung-cap-select'
            }),
            'phieu_nhap': forms.Select(attrs={
                'class': 'form-control select2',
                'id': 'phieu-nhap-select'
            }),
            'loai_cong_no': forms.Select(attrs={
                'class': 'form-control',
                'id': 'loai-cong-no-select'
            }),
            'so_tien': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1000',
                'min': '0',
                'id': 'so-tien-input'
            }),
            'han_thanh_toan': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'han-thanh-toan-input'
            }),
            'ghi_chu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhập ghi chú cho công nợ...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nha_cung_cap'].queryset = NhaCungCap.objects.filter(active=True)
        self.fields['phieu_nhap'].queryset = NhapKho.objects.all()

        # Set default hạn thanh toán (30 ngày từ hôm nay)
        if not self.instance.pk:
            self.fields['han_thanh_toan'].initial = date.today() + timedelta(days=30)

    def clean_so_tien(self):
        so_tien = self.cleaned_data.get('so_tien')
        if so_tien <= 0:
            raise forms.ValidationError("Số tiền phải lớn hơn 0")
        return so_tien

    def clean_han_thanh_toan(self):
        han_thanh_toan = self.cleaned_data.get('han_thanh_toan')
        if han_thanh_toan < date.today():
            raise forms.ValidationError("Hạn thanh toán không được ở trong quá khứ")
        return han_thanh_toan


class ThanhToanCongNoForm(forms.ModelForm):
    so_tien_thanh_toan = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1000',
            'min': '0',
            'id': 'so-tien-thanh-toan-input'
        }),
        label="Số tiền thanh toán"
    )

    ngay_thanh_toan = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'ngay-thanh-toan-input'
        }),
        label="Ngày thanh toán",
        initial=date.today
    )

    class Meta:
        model = LichSuThanhToan
        fields = ['so_tien_thanh_toan', 'ngay_thanh_toan', 'ghi_chu']
        widgets = {
            'ghi_chu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Nhập ghi chú cho thanh toán...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.cong_no = kwargs.pop('cong_no', None)
        super().__init__(*args, **kwargs)

        if self.cong_no:
            self.fields['so_tien_thanh_toan'].widget.attrs['max'] = self.cong_no.so_tien_con_lai

    def clean_so_tien_thanh_toan(self):
        so_tien_thanh_toan = self.cleaned_data.get('so_tien_thanh_toan')

        if not self.cong_no:
            raise forms.ValidationError("Không tìm thấy thông tin công nợ")

        if so_tien_thanh_toan <= 0:
            raise forms.ValidationError("Số tiền thanh toán phải lớn hơn 0")

        if so_tien_thanh_toan > self.cong_no.so_tien_con_lai:
            raise forms.ValidationError(
                f"Số tiền thanh toán không được vượt quá số nợ còn lại ({self.cong_no.so_tien_con_lai:,.0f} VND)")

        return so_tien_thanh_toan

    def clean_ngay_thanh_toan(self):
        ngay_thanh_toan = self.cleaned_data.get('ngay_thanh_toan')
        if ngay_thanh_toan > date.today():
            raise forms.ValidationError("Ngày thanh toán không được ở trong tương lai")
        return ngay_thanh_toan


class TimKiemCongNoForm(forms.Form):
    nha_cung_cap = forms.ModelChoiceField(
        queryset=NhaCungCap.objects.filter(active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'id': 'tim-kiem-nha-cung-cap'
        }),
        label="Nhà cung cấp"
    )

    trang_thai = forms.ChoiceField(
        choices=[('', 'Tất cả')] + CongNoNhaCungCap.TRANG_THAI,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'tim-kiem-trang-thai'
        }),
        label="Trạng thái"
    )

    tu_ngay = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'tu-ngay-input'
        }),
        label="Từ ngày"
    )

    den_ngay = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'den-ngay-input'
        }),
        label="Đến ngày"
    )

    def clean(self):
        cleaned_data = super().clean()
        tu_ngay = cleaned_data.get('tu_ngay')
        den_ngay = cleaned_data.get('den_ngay')

        if tu_ngay and den_ngay and tu_ngay > den_ngay:
            raise forms.ValidationError("Từ ngày không được lớn hơn đến ngày")

        return cleaned_data


class BaoCaoCongNoForm(forms.Form):
    thang = forms.IntegerField(
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '12',
            'id': 'thang-input'
        }),
        label="Tháng",
        initial=date.today().month
    )

    nam = forms.IntegerField(
        min_value=2020,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2100',
            'id': 'nam-input'
        }),
        label="Năm",
        initial=date.today().year
    )

    nha_cung_cap = forms.ModelChoiceField(
        queryset=NhaCungCap.objects.filter(active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'id': 'bao-cao-nha-cung-cap'
        }),
        label="Nhà cung cấp"
    )