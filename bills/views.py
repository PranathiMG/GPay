from rest_framework import serializers, generics, permissions, status
from rest_framework.response import Response
from .models import BillPayment, PaymentReminder
from bank.models import BankAccount
from payments.models import Transaction

class BillPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillPayment
        fields = '__all__'

class PaymentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReminder
        fields = ('id', 'title', 'amount', 'due_date', 'category', 'is_paid')
        read_only_fields = ('id', 'is_paid')

class PaymentReminderListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentReminder.objects.filter(user=self.request.user, is_paid=False).order_by('due_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PaymentReminderDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = PaymentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentReminder.objects.filter(user=self.request.user)

class PayBillSerializer(serializers.Serializer):
    bill_type = serializers.ChoiceField(choices=BillPayment.BILL_TYPE_CHOICES)
    biller_name = serializers.CharField()
    customer_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    upi_pin = serializers.CharField(max_length=6)
    bank_account_id = serializers.IntegerField()

class BillHistoryView(generics.ListAPIView):
    serializer_class = BillPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BillPayment.objects.filter(user=self.request.user).order_by('-timestamp')

class PayBillView(generics.GenericAPIView):
    serializer_class = PayBillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data
            
            # Validate Bank Account & UPI PIN
            try:
                bank_account = BankAccount.objects.get(id=data['bank_account_id'], user=user)
                if bank_account.upi_pin != data['upi_pin']:
                    return Response({"error": "Invalid UPI PIN."}, status=status.HTTP_400_BAD_REQUEST)
                if bank_account.balance < data['amount']:
                    return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
            except BankAccount.DoesNotExist:
                return Response({"error": "Bank account not found."}, status=status.HTTP_404_NOT_FOUND)

            # Deduct balance
            bank_account.balance -= data['amount']
            bank_account.save()

            # Record Bill Payment
            bill_payment = BillPayment.objects.create(
                user=user,
                bill_type=data['bill_type'],
                biller_name=data['biller_name'],
                customer_id=data['customer_id'],
                amount=data['amount'],
                status='success'
            )

            # Also create a transaction record for history
            Transaction.objects.create(
                sender=user,
                receiver=None, # Bill payment to a company/utility
                amount=data['amount'],
                status='success',
                transaction_type='bill' if data['bill_type'] != 'mobile' else 'recharge',
                note=f"Paid {data['bill_type']} bill for {data['biller_name']}"
            )

            return Response({
                "message": "Bill payment successful.",
                "bill_payment": BillPaymentSerializer(bill_payment).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
