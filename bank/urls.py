from django.urls import path
from .views import BankAccountListView, LinkBankAccountView

urlpatterns = [
    path('link/', LinkBankAccountView.as_view(), name='link-bank'),
    path('accounts/', BankAccountListView.as_view(), name='bank-accounts'),
]
