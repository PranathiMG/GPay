# Google Pay (Google Pay Clone) - Setup Guide

## Prerequisites
- Python 3.10+
- Node.js (Optional, for serving frontend if desired)
- Supabase Account (for Production DB)

## 1. Backend Setup (Django)
1. Extract the project.
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt django-cors-headers psycopg2-binary python-dotenv
   ```
4. Configure `.env` file with your Supabase credentials:
   ```
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=YOUR_SUPABASE_PASSWORD
   DB_HOST=YOUR_SUPABASE_HOST
   DB_PORT=5432
   JWT_SECRET=YOUR_JWT_SECRET
   SECRET_KEY=django-insecure-smartpay-clone-secret-key
   DEBUG=True
   ```
5. Run Migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Create an Admin User:
   ```bash
   python manage.py createsuperuser
   ```
7. Start the server:
   ```bash
   python manage.py runserver
   ```

## 2. Frontend Setup
1. The frontend is a Single Page App (SPA) located in the `frontend` folder.
2. Open `frontend/index.html` directly in your browser.
3. Ensure the backend is running at `http://localhost:8000`.

## 3. API Endpoints
### Authentication
- `POST /api/v1/auth/register/` - Register
- `POST /api/v1/auth/login/` - Login (Returns JWT tokens)
- `POST /api/v1/auth/verify-otp/` - Verify Phone (Mock OTP: 123456)
- `POST /api/v1/auth/forgot-password/` - Forgot Password
- `POST /api/v1/auth/reset-password/` - Reset Password

### Bank & Payments
- `POST /api/v1/bank/link/` - Link Bank Account
- `GET /api/v1/bank/accounts/` - List Linked Accounts
- `POST /api/v1/payments/send/` - Send Money
- `GET /api/v1/payments/history/` - Transaction History
- `GET /api/v1/payments/qr-data/` - Get QR Data (UPI ID)

### Bills
- `POST /api/v1/bills/pay/` - Pay Bill
- `GET /api/v1/bills/history/` - Bill History

### Admin
- `GET /api/v1/admin/users/` - View all users
- `GET /api/v1/admin/transactions/` - View all transactions
- `GET /api/v1/admin/reports/` - Aggregate statistics
- `PUT /api/v1/admin/block-user/:id/` - Block/Unblock user

## 4. Supabase Connection Guide
1. Create a new project in Supabase.
2. Go to **Settings > Database**.
3. Copy the Connection details (Host, Name, Port, User, Password).
4. Paste them into the `.env` file in the project root.
5. Ensure your IP is allowed in Supabase settings if required.

## 5. API Testing (Postman)
1. Import the provided (mock) collection or use the endpoints above.
2. For authenticated requests, add `Authorization: Bearer <access_token>` in the Headers.
