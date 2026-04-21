from django.db import models
from django.conf import settings

class BankAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20, unique=True)
    ifsc = models.CharField(max_length=11)
    upi_id = models.CharField(max_length=50, unique=True)
    upi_pin = models.CharField(max_length=6) # Should be hashed in real world, but simulation allows simple storage or basic encryption.
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00) # Start with some mock money
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.upi_id})"
