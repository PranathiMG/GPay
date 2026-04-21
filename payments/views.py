from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Transaction, BillSplit, BillSplitMember
from .serializers import TransactionSerializer, SendMoneySerializer, BillSplitSerializer
from bank.models import BankAccount
from users.models import Notification
from django.db import models

User = get_user_model()

class SendMoneyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SendMoneySerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            identifier = serializer.validated_data['receiver_identifier']
            amount = serializer.validated_data['amount']
            upi_pin = serializer.validated_data['upi_pin']
            bank_account_id = serializer.validated_data['bank_account_id']
            note = serializer.validated_data.get('note', '')

            # 1. Validate Sender Bank Account
            try:
                sender_account = BankAccount.objects.get(id=bank_account_id, user=user)
                if sender_account.upi_pin != upi_pin:
                    return Response({"error": "Invalid UPI PIN."}, status=status.HTTP_400_BAD_REQUEST)
                if sender_account.balance < amount:
                    return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
            except BankAccount.DoesNotExist:
                return Response({"error": "Bank account not found."}, status=status.HTTP_404_NOT_FOUND)

            # 2. Find Receiver
            receiver = None
            receiver_upi_id = None
            
            # Try by phone number
            receiver = User.objects.filter(phone_number=identifier).first()
            if not receiver:
                # Try by UPI ID in bank accounts
                receiver_bank = BankAccount.objects.filter(upi_id=identifier).first()
                if receiver_bank:
                    receiver = receiver_bank.user
                    receiver_upi_id = receiver_bank.upi_id
            
            if not receiver:
                return Response({"error": "Receiver not found."}, status=status.HTTP_404_NOT_FOUND)

            # 3. Process Transaction Atomically
            try:
                with transaction.atomic():
                    # Create transaction record (pending)
                    txn = Transaction.objects.create(
                        sender=user,
                        receiver=receiver,
                        sender_upi_id=sender_account.upi_id,
                        receiver_upi_id=receiver_upi_id or identifier, # Fallback to identifier if found by phone
                        amount=amount,
                        status='pending',
                        note=note
                    )

                    # Update balances
                    sender_account.balance -= amount
                    sender_account.save()
                    
                    # Credit receiver if they have a primary account (simulation)
                    # Let's just find their first active account to credit
                    receiver_account = BankAccount.objects.filter(user=receiver, is_active=True).first()
                    if receiver_account:
                        receiver_account.balance += amount
                        receiver_account.save()
                    
                    txn.status = 'success'
                    txn.save()

                    Notification.objects.create(
                        user=user,
                        message=f"Successfully sent ₹{amount} to {receiver.username if receiver else identifier}."
                    )
                    if receiver:
                        Notification.objects.create(
                            user=receiver,
                            message=f"Received ₹{amount} from {user.username}."
                        )

                    return Response({
                        "message": "Payment successful.",
                        "transaction": TransactionSerializer(txn).data
                    }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": f"Transaction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q
        return Transaction.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')

class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'transaction_id'

class QRCodeDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Generate QR data based on primary bank account's UPI ID
        account = BankAccount.objects.filter(user=request.user).first()
        if not account:
            return Response({"error": "No bank account linked."}, status=status.HTTP_400_BAD_REQUEST)
        
        qr_data = f"upi://pay?pa={account.upi_id}&pn={request.user.username}&mc=0000&mode=02&purpose=00"
        return Response({"upi_id": account.upi_id, "qr_data": qr_data}, status=status.HTTP_200_OK)

class BillSplitCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            description = request.data.get('description')
            total_amount_raw = request.data.get('total_amount')
            if not total_amount_raw:
                return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)
            total_amount = Decimal(str(total_amount_raw))
            member_identifiers = request.data.get('members', [])
        except (ValueError, TypeError, InvalidOperation):
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Clean identifiers: trim and remove creator's own phone number
        cleaned_members = []
        creator_phone = request.user.phone_number
        for m in member_identifiers:
            trimmed = m.strip()
            if trimmed and trimmed != creator_phone and trimmed not in cleaned_members:
                cleaned_members.append(trimmed)

        if not cleaned_members:
            return Response({"error": "No valid other members provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check if creator has enough balance for their share
        total_participants = len(cleaned_members) + 1
        share_amount = (total_amount / total_participants).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Adjust for rounding: last member might pay slightly different, but for simplicity we use uniform share
        # OR: total_amount = share_amount * total_participants (might be off by a few paise)
        
        bank_account = BankAccount.objects.filter(user=request.user).first()
        if not bank_account:
            return Response({"error": "Link a bank account first to create a split."}, status=status.HTTP_400_BAD_REQUEST)
        
        if bank_account.balance < share_amount:
            return Response({"error": f"Insufficient balance to pay your share of ₹{share_amount}."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Deduct from creator
            bank_account.balance -= share_amount
            bank_account.save()

            split = BillSplit.objects.create(
                creator=request.user,
                total_amount=total_amount,
                description=description
            )
            
            # Creator is also a member and has paid
            BillSplitMember.objects.create(
                bill_split=split,
                user=request.user,
                amount=share_amount,
                is_paid=True
            )

            for identifier in cleaned_members:
                member_user = User.objects.filter(phone_number=identifier).first()
                if member_user:
                    BillSplitMember.objects.create(
                        bill_split=split,
                        user=member_user,
                        amount=share_amount
                    )
                else:
                    # Rolling back because of atomic()
                    return Response({"error": f"User with phone {identifier} not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response(BillSplitSerializer(split).data, status=status.HTTP_201_CREATED)

class BillSplitListView(generics.ListAPIView):
    serializer_class = BillSplitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return BillSplit.objects.filter(models.Q(creator=user) | models.Q(members__user=user)).distinct().order_by('-timestamp')

class PaySplitShareView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, split_member_id):
        try:
            member = BillSplitMember.objects.get(id=split_member_id, user=request.user)
            if member.is_paid:
                return Response({"error": "Already paid."}, status=status.HTTP_400_BAD_REQUEST)
            
            upi_pin = request.data.get('upi_pin')
            bank_account = BankAccount.objects.filter(user=request.user).first()
            
            if not bank_account:
                return Response({"error": "No bank account linked."}, status=status.HTTP_400_BAD_REQUEST)
            if bank_account.upi_pin != upi_pin:
                return Response({"error": "Invalid UPI PIN."}, status=status.HTTP_400_BAD_REQUEST)
            if bank_account.balance < member.amount:
                return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                bank_account.balance -= member.amount
                bank_account.save()
                
                creator_account = BankAccount.objects.filter(user=member.bill_split.creator).first()
                if creator_account:
                    creator_account.balance += member.amount
                    creator_account.save()
                
                member.is_paid = True
                member.save()

                if not member.bill_split.members.filter(is_paid=False).exists():
                    member.bill_split.is_completed = True
                    member.bill_split.save()

                return Response({"message": "Share paid successfully."}, status=status.HTTP_200_OK)

        except BillSplitMember.DoesNotExist:
            return Response({"error": "Split share not found."}, status=status.HTTP_404_NOT_FOUND)
