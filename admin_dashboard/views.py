from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from users.serializers import UserSerializer
from payments.models import Transaction
from payments.serializers import TransactionSerializer
from django.db.models import Sum

User = get_user_model()

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

class AdminTransactionListView(generics.ListAPIView):
    queryset = Transaction.objects.all().order_by('-timestamp')
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminRole]

class AdminBlockUserView(views.APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active # Toggle block
            user.save()
            status_msg = "blocked" if not user.is_active else "unblocked"
            
            from .models import AdminLog
            AdminLog.objects.create(
                admin=request.user,
                action=f"{status_msg.capitalize()} user {user.username}"
            )
            
            return Response({"message": f"User {status_msg} successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class AdminReportView(views.APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        total_transactions = Transaction.objects.count()
        total_amount = Transaction.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0
        failed_transactions = Transaction.objects.filter(status='failed').count()
        total_users = User.objects.count()

        return Response({
            "total_users": total_users,
            "total_transactions": total_transactions,
            "total_volume": total_amount,
            "failed_transactions": failed_transactions,
        }, status=status.HTTP_200_OK)
