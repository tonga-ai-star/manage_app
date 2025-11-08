from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from .models import CongNoNhaCungCap, LichSuThanhToan
from .forms import CongNoNhaCungCapForm, ThanhToanCongNoForm, TimKiemCongNoForm, BaoCaoCongNoForm
from datetime import date, datetime
import json


class CongNoListView(ListView):
    model = CongNoNhaCungCap
    template_name = 'debt/congno_list.html'
    context_object_name = 'congno_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('nha_cung_cap', 'phieu_nhap')

        # Áp dụng bộ lọc tìm kiếm
        form = TimKiemCongNoForm(self.request.GET)
        if form.is_valid():
            nha_cung_cap = form.cleaned_data.get('nha_cung_cap')
            trang_thai = form.cleaned_data.get('trang_thai')
            tu_ngay = form.cleaned_data.get('tu_ngay')
            den_ngay = form.cleaned_data.get('den_ngay')

            if nha_cung_cap:
                queryset = queryset.filter(nha_cung_cap=nha_cung_cap)
            if trang_thai:
                queryset = queryset.filter(trang_thai=trang_thai)
            if tu_ngay:
                queryset = queryset.filter(han_thanh_toan__gte=tu_ngay)
            if den_ngay:
                queryset = queryset.filter(han_thanh_toan__lte=den_ngay)

        return queryset.order_by('-han_thanh_toan')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TimKiemCongNoForm(self.request.GET)

        # Thống kê tổng quan
        context['tong_cong_no'] = self.get_queryset().aggregate(
            total=Sum('so_tien')
        )['total'] or 0

        context['tong_con_no'] = self.get_queryset().aggregate(
            total=Sum('so_tien_con_lai')
        )['total'] or 0

        context['so_luong_qua_han'] = self.get_queryset().filter(trang_thai='qua_han').count()

        return context


@login_required
def congno_create(request):
    """Tạo công nợ mới"""
    if request.method == 'POST':
        form = CongNoNhaCungCapForm(request.POST)
        if form.is_valid():
            congno = form.save(commit=False)
            congno.so_tien_con_lai = congno.so_tien  # Khởi tạo số tiền còn lại
            congno.save()

            messages.success(request, f'Tạo công nợ cho {congno.nha_cung_cap.ten} thành công!')
            return redirect('debt:congno_list')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin nhập!')
    else:
        form = CongNoNhaCungCapForm()

    context = {
        'form': form,
        'title': 'Tạo Công Nợ Mới'
    }
    return render(request, 'debt/congno_form.html', context)


class CongNoUpdateView(UpdateView):
    model = CongNoNhaCungCap
    form_class = CongNoNhaCungCapForm
    template_name = 'debt/congno_form.html'
    success_url = reverse_lazy('debt:congno_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cập nhật Công Nợ'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Cập nhật công nợ thành công!')
        return super().form_valid(form)


class CongNoDetailView(DetailView):
    model = CongNoNhaCungCap
    template_name = 'debt/congno_detail.html'
    context_object_name = 'congno'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lich_su_thanh_toan'] = self.object.lich_su_thanh_toan.all()
        context['thanh_toan_form'] = ThanhToanCongNoForm(cong_no=self.object)
        return context


@login_required
def thanh_toan_cong_no(request, pk):
    """Xử lý thanh toán công nợ"""
    congno = get_object_or_404(CongNoNhaCungCap, pk=pk)

    if request.method == 'POST':
        form = ThanhToanCongNoForm(request.POST, cong_no=congno)
        if form.is_valid():
            try:
                so_tien_thanh_toan = form.cleaned_data['so_tien_thanh_toan']
                ngay_thanh_toan = form.cleaned_data['ngay_thanh_toan']
                ghi_chu = form.cleaned_data['ghi_chu']

                # Thực hiện thanh toán
                congno.thanh_toan(so_tien_thanh_toan, ngay_thanh_toan)

                messages.success(request, f'Thanh toán {so_tien_thanh_toan:,.0f} VND thành công!')
                return redirect('debt:congno_detail', pk=congno.pk)

            except Exception as e:
                messages.error(request, f'Lỗi khi thanh toán: {str(e)}')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin thanh toán!')

    return redirect('debt:congno_detail', pk=congno.pk)


@login_required
def congno_delete(request, pk):
    """Xóa công nợ"""
    congno = get_object_or_404(CongNoNhaCungCap, pk=pk)

    if request.method == 'POST':
        try:
            ten_nha_cung_cap = congno.nha_cung_cap.ten
            congno.delete()
            messages.success(request, f'Đã xóa công nợ của {ten_nha_cung_cap}')
            return redirect('debt:congno_list')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa: {str(e)}')

    context = {'congno': congno}
    return render(request, 'debt/congno_confirm_delete.html', context)


def bao_cao_cong_no(request):
    """Báo cáo công nợ"""
    form = BaoCaoCongNoForm(request.GET or None)
    congno_list = None
    thong_ke = None

    if form.is_valid():
        thang = form.cleaned_data['thang']
        nam = form.cleaned_data['nam']
        nha_cung_cap = form.cleaned_data['nha_cung_cap']

        # Lọc dữ liệu theo tiêu chí
        filters = Q(han_thanh_toan__month=thang, han_thanh_toan__year=nam)
        if nha_cung_cap:
            filters &= Q(nha_cung_cap=nha_cung_cap)

        congno_list = CongNoNhaCungCap.objects.filter(filters).select_related('nha_cung_cap')

        # Thống kê
        thong_ke = congno_list.aggregate(
            tong_so_tien=Sum('so_tien'),
            tong_con_lai=Sum('so_tien_con_lai'),
            tong_da_thanh_toan=Sum('so_tien') - Sum('so_tien_con_lai')
        )

    context = {
        'form': form,
        'congno_list': congno_list,
        'thong_ke': thong_ke,
        'title': 'Báo Cáo Công Nợ'
    }
    return render(request, 'debt/bao_cao_cong_no.html', context)


def get_phieu_nhap_theo_nha_cung_cap(request, nha_cung_cap_id):
    """API lấy danh sách phiếu nhập theo nhà cung cấp"""
    try:
        from inventory.models import NhapKho
        phieu_nhap_list = NhapKho.objects.filter(
            nha_cung_cap_id=nha_cung_cap_id
        ).values('id', 'ma_phieu', 'tong_tien')

        return JsonResponse(list(phieu_nhap_list), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)