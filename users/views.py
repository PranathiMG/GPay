from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer, UserSerializer, VerifyOTPSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, MyTokenObtainPairSerializer
)

User = get_user_model()

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

from django.db import transaction
from decimal import Decimal
from bank.models import BankAccount
from payments.models import Transaction

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Handle referral logic
            ref_code = request.data.get('referral_code')
            referrer = None
            if ref_code:
                referrer = User.objects.filter(referral_code=ref_code).first()

            with transaction.atomic():
                user = serializer.save()
                
                # If referrer found, credit them 200
                if referrer:
                    ref_account = BankAccount.objects.filter(user=referrer).first()
                    if ref_account:
                        ref_account.balance += Decimal('200.00')
                        ref_account.save()
                        
                        # Create referral transaction record
                        Transaction.objects.create(
                            sender=None, # System bonus
                            receiver=referrer,
                            receiver_upi_id=ref_account.upi_id,
                            amount=Decimal('200.00'),
                            status='success',
                            transaction_type='referral',
                            note=f"Referral bonus for inviting {user.username}"
                        )
                        
                        from .models import Notification
                        Notification.objects.create(
                            user=referrer,
                            message=f"Congratulations! You earned ₹200 for referring {user.username}."
                        )

            return Response({
                "message": "User registered successfully. Use OTP 123456 to verify.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(phone_number=phone_number)
                if user.otp == otp:
                    user.is_verified = True
                    user.otp = None
                    user.save()
                    return Response({"message": "Phone verified successfully."}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                user.otp = "654321" # Mock reset OTP
                user.save()
                return Response({"message": "Reset OTP sent to email. Use 654321."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "Email not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            try:
                user = User.objects.get(email=email)
                if user.otp == otp:
                    user.set_password(new_password)
                    user.otp = None
                    user.save()
                    return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token or refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)
