from django.contrib import admin
from django.urls import path, include
from users.views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/bank/', include('bank.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/bills/', include('bills.urls')),
    path('api/v1/admin/', include('admin_dashboard.urls')),
    path('health', HealthView.as_view(), name='root_health'),
]
