from django.urls import path
from .views import AdminUserListView, AdminTransactionListView, AdminBlockUserView, AdminReportView

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin-users'),
    path('transactions/', AdminTransactionListView.as_view(), name='admin-transactions'),
    path('reports/', AdminReportView.as_view(), name='admin-reports'),
    path('block-user/<int:pk>/', AdminBlockUserView.as_view(), name='admin-block-user'),
]
