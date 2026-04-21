from django.db import models
from django.conf import settings

class BillPayment(models.Model):
    BILL_TYPE_CHOICES = (
        ('mobile', 'Mobile Recharge'),
        ('electricity', 'Electricity Bill'),
        ('dth', 'DTH'),
        ('broadband', 'Broadband'),
        ('rent', 'Rent'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bill_type = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES)
    biller_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=50) # phone number for recharge, CA number for electricity
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, default='success')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bill_type} - {self.amount} ({self.status})"

class PaymentReminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    category = models.CharField(max_length=20, choices=BillPayment.BILL_TYPE_CHOICES)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount} (Due: {self.due_date})"
