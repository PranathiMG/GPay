from rest_framework import serializers
from .models import Transaction, BillSplit, BillSplitMember

class BillSplitMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BillSplitMember
        fields = ('id', 'user', 'username', 'amount', 'is_paid')

class BillSplitSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    members = BillSplitMemberSerializer(many=True, read_only=True)

    class Meta:
        model = BillSplit
        fields = ('id', 'creator', 'creator_name', 'total_amount', 'description', 'is_completed', 'timestamp', 'members')
        read_only_fields = ('creator', 'is_completed')

class TransactionSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'

class SendMoneySerializer(serializers.Serializer):
    # Support sending by phone number or UPI ID
    receiver_identifier = serializers.CharField() 
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    upi_pin = serializers.CharField(max_length=6)
    note = serializers.CharField(required=False, allow_blank=True)
    bank_account_id = serializers.IntegerField() # From which account to send
