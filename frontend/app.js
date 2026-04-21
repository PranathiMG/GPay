console.log("Google Pay App JS Loaded");
const API_BASE = 'http://localhost:8000/api/v1';
let user = null;
let token = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

// Axios Configuration
const api = axios.create({ baseURL: API_BASE });
if (token) api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Helper: Show View
function showView(viewId) {
    console.log("Switching to view:", viewId);
    const role = localStorage.getItem('user_role');
    
    if (role === 'merchant' && (viewId === 'split-bill' || viewId === 'bills')) {
        return showView('dashboard');
    }

    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const targetView = document.getElementById(viewId + '-view');
    if (targetView) targetView.classList.remove('hidden');
    
    const sidebar = document.getElementById('sidebar');
    if (['login', 'register', 'otp'].includes(viewId)) {
        sidebar.classList.add('hidden');
    } else {
        sidebar.classList.remove('hidden');
        
        const billsLink = document.getElementById('bills-link');
        const splitLink = document.getElementById('split-bill-link');
        const adminLink = document.getElementById('admin-link');

        if (role === 'merchant') {
            if (billsLink) billsLink.style.display = 'none';
            if (splitLink) splitLink.style.display = 'none';
        } else {
            if (billsLink) billsLink.style.display = 'block';
            if (splitLink) splitLink.style.display = 'block';
        }
        
        if (role === 'admin') adminLink.style.display = 'block';
        else adminLink.style.display = 'none';

        if (viewId === 'dashboard') {
            loadDashboardData();
        } else if (viewId === 'history') {
            loadHistoryData();
        } else if (viewId === 'qr-scan') {
            loadQRData();
        } else if (viewId === 'send-money' || viewId === 'bills') {
            loadBankAccounts();
        } else if (viewId === 'split-bill') {
            loadSplitData();
        } else if (viewId === 'admin-dashboard') {
            loadAdminData();
        } else if (viewId === 'reminders') {
            loadRemindersData();
        } else if (viewId === 'refer-earn') {
            const codeDisplay = document.getElementById('my-referral-code');
            let code = localStorage.getItem('user_referral');
            
            if (!code || code === "undefined" || code === "null" || code === "------") {
                codeDisplay.innerText = "Loading...";
                api.get('/auth/profile/')
                    .then(res => {
                        const newCode = res.data.referral_code;
                        if (newCode) {
                            localStorage.setItem('user_referral', newCode);
                            codeDisplay.innerText = newCode;
                        } else {
                            codeDisplay.innerText = "NOT-AVAILABLE";
                        }
                    })
                    .catch(err => {
                        console.error("Profile fetch error:", err);
                        codeDisplay.innerText = "NOT-AVAILABLE";
                    });
            } else {
                codeDisplay.innerText = code;
            }
        }
    }
}

// Global functions for onclick
window.showView = showView;
window.copyReferralCode = function() {
    const code = document.getElementById('my-referral-code').innerText;
    if (code === "NOT-AVAILABLE" || code === "------" || code === "Loading...") {
        return toast("No code available to copy.");
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code).then(() => {
            toast("Referral code copied!");
        }).catch(err => {
            console.error("Clipboard copy failed:", err);
            fallbackCopyTextToClipboard(code);
        });
    } else {
        fallbackCopyTextToClipboard(code);
    }
};

window.handleLogin = async function(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    try {
        const res = await api.post('/auth/login/', { username, password });
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        localStorage.setItem('user_role', res.data.role);
        localStorage.setItem('user_name', res.data.username);
        localStorage.setItem('user_phone', res.data.phone || "9876543210");
        localStorage.setItem('user_referral', res.data.referral_code);
        api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access}`;
        toast("Login successful!");
        showView('dashboard');
    } catch (err) {
        toast("Login failed: " + (err.response?.data?.detail || "Invalid credentials"));
    }
};

window.handleRegister = async function(e) {
    e.preventDefault();
    const data = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        phone_number: document.getElementById('reg-phone').value,
        password: document.getElementById('reg-password').value,
        referral_code: document.getElementById('reg-referral').value
    };
    try {
        const res = await api.post('/auth/register/', data);
        document.getElementById('otp-phone').value = data.phone_number;
        toast(res.data.message);
        showView('otp');
    } catch (err) {
        toast("Registration failed: " + JSON.stringify(err.response?.data));
    }
};

window.handleVerifyOTP = async function(e) {
    e.preventDefault();
    const phone_number = document.getElementById('otp-phone').value;
    const otp = document.getElementById('otp-input').value;
    try {
        await api.post('/auth/verify-otp/', { phone_number, otp });
        toast("Verified! You can now login.");
        showView('login');
    } catch (err) {
        toast("Verification failed.");
    }
};

window.logout = function() {
    localStorage.clear();
    delete api.defaults.headers.common['Authorization'];
    showView('login');
};

window.handleLinkBank = async function(e) {
    e.preventDefault();
    const data = {
        bank_name: document.getElementById('bank-name').value,
        account_number: document.getElementById('account-number').value,
        ifsc: document.getElementById('ifsc').value,
        upi_pin: document.getElementById('upi-pin').value
    };
    try {
        await api.post('/bank/link/', data);
        showSuccess("Account Linked", "Your bank account has been successfully linked to Google Pay.");
        showView('dashboard');
    } catch (err) {
        toast("Linking failed.");
    }
};

window.handleSendMoney = async function(e) {
    e.preventDefault();
    const data = {
        receiver_identifier: document.getElementById('send-identifier').value,
        amount: document.getElementById('send-amount').value,
        note: document.getElementById('send-note').value,
        bank_account_id: document.getElementById('send-bank-account').value,
        upi_pin: document.getElementById('send-upi-pin').value
    };
    try {
        await api.post('/payments/send/', data);
        showSuccess("Payment Sent", `₹ ${data.amount} sent to ${data.receiver_identifier} successfully.`);
        showView('dashboard');
    } catch (err) {
        toast("Payment failed: " + (err.response?.data?.error || "Check details"));
    }
};

window.handleScanManual = function() {
    const id = document.getElementById('scan-manual-id').value;
    if (!id) return toast("Enter UPI ID");
    document.getElementById('send-identifier').value = id;
    showView('send-money');
};

window.openBillModal = function(type) {
    console.log("Opening bill modal for type:", type);
    const modalTypeInput = document.getElementById('bill-type');
    if (modalTypeInput) modalTypeInput.value = type;
    const modalTitle = document.getElementById('bill-modal-title');
    if (modalTitle) modalTitle.innerText = "Pay " + type.charAt(0).toUpperCase() + type.slice(1);
    
    document.getElementById('bill-amount').value = '';
    document.getElementById('biller-name').value = '';
    document.getElementById('customer-id').value = '';
    
    const plansList = document.getElementById('plans-list');
    if (plansList) {
        const plans = BILL_PLANS[type] || [];
        if (plans.length > 0) {
            plansList.innerHTML = plans.map(p => `
                <div class="plan-card" onclick="selectBillPlan(${p.amount}, this)" 
                     style="border: 1px solid #dadce0; padding: 12px; border-radius: 8px; cursor: pointer; transition: all 0.2s; background: white;">
                    <div style="font-weight: bold; color: var(--primary); font-size: 18px;">₹${p.amount}</div>
                    <div style="font-size: 13px; margin: 6px 0; font-weight: 500;">${p.data} | ${p.validity}</div>
                    <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.4;">${p.desc}</div>
                </div>
            `).join('');
        } else {
            plansList.innerHTML = '<p style="grid-column: span 2; color: var(--text-secondary); font-size: 13px;">No pre-set plans available. Please enter amount manually.</p>';
        }
    }
    document.getElementById('bill-modal').classList.remove('hidden');
    loadBankAccounts();
};

window.handlePayBill = async function(e) {
    e.preventDefault();
    const data = {
        bill_type: document.getElementById('bill-type').value,
        biller_name: document.getElementById('biller-name').value,
        customer_id: document.getElementById('customer-id').value,
        amount: document.getElementById('bill-amount').value,
        bank_account_id: document.getElementById('bill-bank-account').value,
        upi_pin: document.getElementById('bill-upi-pin').value
    };
    try {
        await api.post('/bills/pay/', data);
        closeModal('bill-modal');
        showSuccess("Bill Paid", `₹ ${data.amount} paid for ${data.bill_type} successfully.`);
        showView('dashboard');
    } catch (err) {
        toast("Bill payment failed.");
    }
};

window.handleCreateSplit = async function(e) {
    e.preventDefault();
    const rawMembers = document.getElementById('split-members').value.split('\n');
    const data = {
        description: document.getElementById('split-desc').value,
        total_amount: document.getElementById('split-total').value,
        members: rawMembers.map(m => m.trim()).filter(m => m !== '')
    };
    try {
        await api.post('/payments/split/create/', data);
        toast("Split created successfully!");
        e.target.reset();
        loadSplitData();
    } catch (err) {
        toast("Failed to create split: " + (err.response?.data?.error || "Check members"));
    }
};

window.handlePaySplitShare = async function(memberId) {
    const details = "Authorize payment of your share for this split bill.";
    openPaymentModal(details, async (pin) => {
        try {
            await api.post(`/payments/split/pay/${memberId}/`, { upi_pin: pin });
            showSuccess("Payment Successful", "Your share has been paid securely.");
            loadSplitData();
            loadDashboardData();
        } catch (err) {
            toast("Payment failed: " + (err.response?.data?.error || "Check details"));
        }
    });
};

window.toggleUserStatus = async function(id) {
    try {
        await api.put(`/admin/block-user/${id}/`);
        toast("User status updated.");
        loadAdminData();
    } catch (err) {}
};

window.closeModal = function(id) {
    document.getElementById(id).classList.add('hidden');
};

window.closePaymentModal = function() {
    document.getElementById('payment-modal').classList.add('hidden');
};

window.selectBillPlan = function(amount, element) {
    document.getElementById('bill-amount').value = amount;
    document.querySelectorAll('.plan-card').forEach(c => {
        c.style.borderColor = '#dadce0';
        c.style.backgroundColor = 'white';
    });
    element.style.borderColor = 'var(--primary)';
    element.style.backgroundColor = '#f8faff';
};

// Utils
function toast(message) {
    const container = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerText = message;
    container.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

function showSuccess(title, message) {
    document.getElementById('success-title').innerText = title;
    document.getElementById('success-message').innerText = message;
    document.getElementById('success-modal').classList.remove('hidden');
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        toast("Referral code copied!");
    } catch (err) {
        toast("Unable to copy code.");
    }
    document.body.removeChild(textArea);
}

async function loadDashboardData() {
    const role = localStorage.getItem('user_role');
    const name = localStorage.getItem('user_name');
    document.getElementById('display-name').innerText = name || "User";
    try {
        const res = await api.get('/bank/accounts/');
        const accounts = res.data;
        const total = accounts.reduce((acc, curr) => acc + parseFloat(curr.balance), 0);
        document.getElementById('total-balance').innerText = `₹ ${total.toFixed(2)}`;
        if (accounts.length > 0) document.getElementById('display-upi').innerText = accounts[0].upi_id;

        const actionsDiv = document.querySelector('#dashboard-view .actions');
        actionsDiv.innerHTML = `<button onclick="showView('link-bank')">Link Bank Account</button>`;
        
        updateDashboardReminders();

        const histRes = await api.get('/payments/history/');
        const recentList = document.getElementById('recent-history-list');
        if (histRes.data.length === 0) {
            recentList.innerHTML = '<li>No recent transactions.</li>';
        } else {
            recentList.innerHTML = histRes.data.slice(0, 5).map(txn => `
                <li style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee;">
                    <span><strong>${txn.receiver_name || 'Utility'}</strong><br><small>${new Date(txn.timestamp).toLocaleDateString()}</small></span>
                    <span style="color: ${txn.sender_name === name ? 'red' : 'green'}">${txn.sender_name === name ? '-' : '+'} ₹${txn.amount}</span>
                </li>
            `).join('');
        }
    } catch (err) {
        if (err.response?.status === 401) logout();
    }
}

async function loadBankAccounts() {
    try {
        const res = await api.get('/bank/accounts/');
        const selects = ['send-bank-account', 'bill-bank-account'];
        if (res.data.length === 0) {
            selects.forEach(sid => document.getElementById(sid).innerHTML = '<option value="">-- No bank accounts linked --</option>');
            return;
        }
        selects.forEach(sid => {
            document.getElementById(sid).innerHTML = res.data.map(acc => `<option value="${acc.id}">${acc.bank_name} - ${acc.upi_id} (Bal: ₹${acc.balance})</option>`).join('');
        });
    } catch (err) {}
}

async function loadHistoryData() {
    try {
        const res = await api.get('/payments/history/');
        document.getElementById('history-body').innerHTML = res.data.map(txn => `
            <tr>
                <td>${new Date(txn.timestamp).toLocaleDateString()}</td>
                <td><strong>${txn.transaction_type.toUpperCase()}</strong><br><small>${txn.sender_name} ➔ ${txn.receiver_name || 'Utility'}</small></td>
                <td>₹ ${txn.amount}</td>
                <td style="color: ${txn.status === 'success' ? 'green' : 'red'}">${txn.status.toUpperCase()}</td>
            </tr>
        `).join('');
    } catch (err) {}
}

async function loadQRData() {
    try {
        const res = await api.get('/payments/qr-data/');
        document.getElementById('qr-upi-id').innerText = res.data.upi_id;
        QRCode.toCanvas(document.getElementById('qr-code'), res.data.qr_data, { width: 200 });
    } catch (err) {}
}

async function loadSplitData() {
    try {
        const res = await api.get('/payments/split/list/');
        const list = document.getElementById('split-list');
        const currentUserName = localStorage.getItem('user_name');
        if (res.data.length === 0) {
            list.innerHTML = '<p class="text-center" style="color: var(--text-secondary); margin-top: 20px;">No split bills yet.</p>';
            return;
        }
        list.innerHTML = res.data.map(split => `
            <div class="card" style="margin: 10px 0; max-width: 100%; border-left: 4px solid ${split.is_completed ? 'var(--success)' : 'var(--primary)'}">
                <div style="display: flex; justify-content: space-between; align-items: center;"><h4>${split.description}</h4><span style="font-weight: bold; color: var(--primary)">₹${split.total_amount}</span></div>
                <p><small>Created by ${split.creator_name === currentUserName ? 'You' : split.creator_name}</small></p>
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
                <ul style="list-style: none; padding: 0;">
                    ${split.members.map(m => `
                        <li style="display: flex; justify-content: space-between; align-items: center; padding: 5px 0;">
                            <span>${m.username === currentUserName ? '<strong>You</strong>' : m.username}</span>
                            <span>₹${parseFloat(m.amount).toFixed(2)} ${m.is_paid ? '<span style="color: var(--success); margin-left: 10px;">✔️ Paid</span>' : (m.username === currentUserName ? `<button onclick="handlePaySplitShare(${m.id})" style="padding: 4px 8px; font-size: 12px; width: auto; margin-left: 10px; display: inline-block; margin-bottom: 0;">Pay Now</button>` : '<span style="color: orange; margin-left: 10px;">⏳ Pending</span>')}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadAdminData() {
    try {
        const stats = await api.get('/admin/reports/');
        document.getElementById('admin-total-users').innerText = stats.data.total_users;
        document.getElementById('admin-total-volume').innerText = `₹ ${stats.data.total_volume}`;
        document.getElementById('admin-failed-txns').innerText = stats.data.failed_transactions;
        const users = await api.get('/admin/users/');
        document.getElementById('admin-users-list').innerHTML = `<table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>${users.data.map(u => `<tr><td>${u.username} (${u.email})</td><td>${u.role}</td><td>${u.is_verified ? 'Verified' : 'Unverified'}</td><td><button class="secondary" onclick="toggleUserStatus(${u.id})">${u.is_active ? 'Block' : 'Unblock'}</button></td></tr>`).join('')}</tbody></table>`;
    } catch (err) {
        showView('dashboard');
    }
}

// Payment Verification Modal Logic
window.openPaymentModal = function(details, onConfirm) {
    document.getElementById('payment-modal-details').innerText = details;
    document.getElementById('modal-payment-pin').value = '';
    const phone = localStorage.getItem('user_phone') || "9876543210";
    const masked = phone.substring(0, 2) + "******" + phone.substring(phone.length - 2);
    document.getElementById('modal-masked-phone').innerText = "+91 " + masked;
    document.getElementById('payment-modal').classList.remove('hidden');
    document.getElementById('modal-payment-pin').focus();
    const confirmBtn = document.getElementById('confirm-payment-btn');
    const newBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
    newBtn.onclick = () => {
        const pin = document.getElementById('modal-payment-pin').value;
        if (pin.length === 6) { onConfirm(pin); closePaymentModal(); } else { toast("Please enter a 6-digit code."); }
    };
};

const BILL_PLANS = {
    mobile: [{id:1,amount:239,data:'1.5GB/day',validity:'28 Days',desc:'Unlimited Voice'},{id:2,amount:299,data:'2GB/day',validity:'28 Days',desc:'Unlimited Voice + 100 SMS'},{id:3,amount:666,data:'1.5GB/day',validity:'84 Days',desc:'Best Seller'},{id:4,amount:2999,data:'2.5GB/day',validity:'365 Days',desc:'Annual Plan'}],
    dth: [{id:5,amount:350,data:'Basic HD',validity:'1 Month',desc:'All FTA + Sports'},{id:6,amount:550,data:'Premium 4K',validity:'1 Month',desc:'All HD Channels'},{id:7,amount:1800,data:'Value Pack',validity:'6 Months',desc:'Regional + News'}],
    electricity: [{id:8,amount:500,data:'Min Deposit',validity:'N/A',desc:'Add balance to meter'},{id:9,amount:1200,data:'Avg Usage',validity:'N/A',desc:'Estimated monthly bill'},{id:10,amount:2500,data:'High Usage',validity:'N/A',desc:'Commercial/AC use'}],
    broadband: [{id:11,amount:499,data:'40 Mbps',validity:'1 Month',desc:'Unlimited Data'},{id:12,amount:999,data:'200 Mbps',validity:'1 Month',desc:'Free OTT Subscription'},{id:13,amount:1499,data:'1 Gbps',validity:'1 Month',desc:'Extreme Speed'}]
};

// --- REMINDERS LOGIC ---
window.openAddReminderModal = function() {
    document.getElementById('add-reminder-modal').classList.remove('hidden');
};

window.handleCreateReminder = async function(e) {
    e.preventDefault();
    const data = {
        title: document.getElementById('rem-title').value,
        amount: document.getElementById('rem-amount').value,
        due_date: document.getElementById('rem-date').value,
        category: document.getElementById('rem-category').value
    };
    try {
        await api.post('/bills/reminders/', data);
        toast("Reminder set successfully!");
        closeModal('add-reminder-modal');
        e.target.reset();
        loadRemindersData();
        updateDashboardReminders();
    } catch (err) {
        toast("Failed to set reminder.");
    }
};

window.loadRemindersData = async function() {
    try {
        const res = await api.get('/bills/reminders/');
        const list = document.getElementById('reminders-list');
        if (res.data.length === 0) {
            list.innerHTML = '<p class="text-center" style="grid-column: span 2; color: var(--text-secondary); padding: 40px;">No upcoming reminders. Relax!</p>';
            return;
        }

        list.innerHTML = res.data.map(rem => `
            <div class="card" style="border-left: 4px solid var(--primary); display: flex; justify-content: space-between; align-items: center; padding: 15px;">
                <div>
                    <h4 style="margin: 0;">${rem.title}</h4>
                    <p style="font-size: 13px; color: var(--text-secondary); margin: 4px 0;">Due: ${new Date(rem.due_date).toLocaleDateString()} | ${rem.category.toUpperCase()}</p>
                    <div style="font-weight: bold; color: var(--primary); font-size: 18px;">₹ ${rem.amount}</div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <button onclick="payReminder(${rem.id}, '${rem.amount}', '${rem.category}', '${rem.title}')" style="margin-bottom: 0; padding: 6px 12px; font-size: 12px;">Pay Now</button>
                    <button class="secondary" onclick="deleteReminder(${rem.id})" style="margin-bottom: 0; padding: 6px 12px; font-size: 12px; border-color: var(--danger); color: var(--danger);">Dismiss</button>
                </div>
            </div>
        `).join('');
    } catch (err) {}
};

window.deleteReminder = async function(id) {
    if (!confirm("Are you sure you want to dismiss this reminder?")) return;
    try {
        await api.delete(`/bills/reminders/${id}/`);
        toast("Reminder dismissed.");
        loadRemindersData();
        updateDashboardReminders();
    } catch (err) {
        toast("Failed to delete reminder.");
    }
};

window.payReminder = function(id, amount, category, title) {
    showView('bills');
    setTimeout(() => {
        openBillModal(category);
        document.getElementById('bill-amount').value = amount;
        document.getElementById('biller-name').value = title;
    }, 100);
};

async function updateDashboardReminders() {
    try {
        const res = await api.get('/bills/reminders/');
        const list = document.getElementById('dashboard-reminders-list');
        if (res.data.length === 0) {
            list.innerHTML = '<p style="grid-column: span 2; color: var(--text-secondary); font-size: 13px;">All clear! No upcoming payments.</p>';
            return;
        }

        list.innerHTML = res.data.slice(0, 2).map(rem => `
            <div class="stat-card" style="padding: 12px; border-left: 3px solid var(--primary);">
                <div style="font-size: 11px; text-transform: uppercase; color: var(--text-secondary);">${rem.category}</div>
                <div style="font-weight: bold; margin: 4px 0;">${rem.title}</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: var(--primary); font-weight: 600;">₹ ${rem.amount}</span>
                    <span style="font-size: 11px; color: var(--danger);">Due: ${new Date(rem.due_date).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

// Start App
if (token) {
    showView('dashboard');
    updateDashboardReminders();
} else {
    showView('login');
}
