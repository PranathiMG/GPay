from rest_framework import serializers
from .models import BankAccount

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('id', 'bank_name', 'account_number', 'ifsc', 'upi_id', 'balance')
        read_only_fields = ('balance', 'upi_id')

class LinkBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('bank_name', 'account_number', 'ifsc', 'upi_pin')

    def create(self, validated_data):
        user = self.context['request'].user
        # Generate a simple UPI ID: username@bank
        upi_id = f"{user.username}@{validated_data['bank_name'].lower().replace(' ', '')}"
        return BankAccount.objects.create(user=user, upi_id=upi_id, **validated_data)
