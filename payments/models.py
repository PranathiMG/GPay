import uuid
from django.db import models
from django.conf import settings

class Transaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    TYPE_CHOICES = (
        ('p2p', 'Peer-to-Peer'),
        ('merchant', 'Merchant Payment'),
        ('bill', 'Bill Payment'),
        ('recharge', 'Mobile Recharge'),
        ('referral', 'Referral Bonus'),
    )

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_transactions', on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_transactions', on_delete=models.CASCADE, null=True, blank=True)
    
    # We can also store UPI IDs directly for reference
    sender_upi_id = models.CharField(max_length=50, null=True, blank=True)
    receiver_upi_id = models.CharField(max_length=50, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transaction_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='p2p')
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} ({self.status})"

class BillSplit(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_splits')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Split: {self.description} by {self.creator.username}"

class BillSplitMember(models.Model):
    bill_split = models.ForeignKey(BillSplit, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.amount} (Paid: {self.is_paid})"
