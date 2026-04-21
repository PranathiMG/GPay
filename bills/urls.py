from django.urls import path
from .views import PayBillView, BillHistoryView, PaymentReminderListCreateView, PaymentReminderDetailView

urlpatterns = [
    path('pay/', PayBillView.as_view(), name='pay-bill'),
    path('history/', BillHistoryView.as_view(), name='bill-history'),
    path('reminders/', PaymentReminderListCreateView.as_view(), name='reminder-list'),
    path('reminders/<int:pk>/', PaymentReminderDetailView.as_view(), name='reminder-detail'),
]
