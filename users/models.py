from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('merchant', 'Merchant'),
        ('admin', 'Admin'),
    )
    
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    referral_code = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import uuid
            self.referral_code = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"

