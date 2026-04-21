from django.urls import path
from .views import (
    SendMoneyView, TransactionHistoryView, TransactionDetailView, QRCodeDataView,
    BillSplitCreateView, BillSplitListView, PaySplitShareView
)

urlpatterns = [
    path('send/', SendMoneyView.as_view(), name='send-money'),
    path('history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('qr-data/', QRCodeDataView.as_view(), name='qr-data'),
    path('split/create/', BillSplitCreateView.as_view(), name='split-create'),
    path('split/list/', BillSplitListView.as_view(), name='split-list'),
    path('split/pay/<int:split_member_id>/', PaySplitShareView.as_view(), name='split-pay'),
    path('<uuid:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
]
