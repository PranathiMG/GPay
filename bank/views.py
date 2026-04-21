from rest_framework import generics, permissions
from .models import BankAccount
from .serializers import BankAccountSerializer, LinkBankAccountSerializer
from users.models import Notification

class BankAccountListView(generics.ListAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)

class LinkBankAccountView(generics.CreateAPIView):
    serializer_class = LinkBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        account = serializer.save()
        Notification.objects.create(
            user=self.request.user,
            message=f"Successfully linked bank account: {account.bank_name} ({account.account_number[-4:]})"
        )

