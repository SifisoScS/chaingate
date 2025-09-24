// ChainGate Main Application JavaScript
class ChainGateApp {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.socket = null;
        this.init();
    }

    async init() {
        // Hide loading screen after a short delay
        setTimeout(() => {
            document.getElementById('loadingScreen').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');
        }, 1500);

        // Check authentication status
        await this.checkAuthStatus();
        
        // Initialize WebSocket connection
        this.initializeWebSocket();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Show appropriate screen
        this.showAppropriateScreen();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.is_authenticated) {
                this.currentUser = data;
                this.isAuthenticated = true;
                this.updateUserInterface();
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
        }
    }

    setupEventListeners() {
        // Auth buttons
        document.getElementById('loginBtn').addEventListener('click', () => this.showLoginModal());
        document.getElementById('registerBtn').addEventListener('click', () => this.showRegisterModal());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());

        // Modal close buttons
        document.getElementById('closeLoginModal').addEventListener('click', () => this.hideLoginModal());
        document.getElementById('closeRegisterModal').addEventListener('click', () => this.hideRegisterModal());
        document.getElementById('closeDepositModal').addEventListener('click', () => this.hideDepositModal());
        document.getElementById('closeWithdrawModal').addEventListener('click', () => this.hideWithdrawModal());

        // Forms
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('withdrawForm').addEventListener('submit', (e) => this.handleWithdraw(e));

        // Player dashboard buttons
        document.getElementById('depositBtn').addEventListener('click', () => this.showDepositModal());
        document.getElementById('withdrawBtn').addEventListener('click', () => this.showWithdrawModal());
        document.getElementById('simulateDepositBtn').addEventListener('click', () => this.simulateDeposit());
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshPlayerData());
        document.getElementById('copyAddressBtn').addEventListener('click', () => this.copyWalletAddress());



        // Close modals when clicking outside
        this.setupModalCloseOnOutsideClick();
    }

    setupModalCloseOnOutsideClick() {
        const modals = ['loginModal', 'registerModal', 'depositModal', 'withdrawModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        });
    }

    showAppropriateScreen() {
        if (this.isAuthenticated) {
            this.showPlayerDashboard();
        } else {
            this.showWelcomeScreen();
        }
    }

    showWelcomeScreen() {
        document.getElementById('welcomeScreen').classList.remove('hidden');
        document.getElementById('playerDashboard').classList.add('hidden');
    }

    showPlayerDashboard() {
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('playerDashboard').classList.remove('hidden');

        // Load player data
        this.loadPlayerData();
    }



    updateUserInterface() {
        if (this.isAuthenticated) {
            document.getElementById('authButtons').classList.add('hidden');
            document.getElementById('userInfo').classList.remove('hidden');
            document.getElementById('userInfo').classList.add('flex');
            
            document.getElementById('userName').textContent = this.currentUser.username;
            
            const roleElement = document.getElementById('userRole');
            roleElement.textContent = this.currentUser.role.toUpperCase();
            roleElement.className = 'px-2 py-1 rounded-full text-xs font-medium bg-blue-600';

            // Admin button removed as per user request
        } else {
            document.getElementById('authButtons').classList.remove('hidden');
            document.getElementById('userInfo').classList.add('hidden');
        }
    }

    // Modal functions
    showLoginModal() {
        document.getElementById('loginModal').classList.remove('hidden');
        document.getElementById('loginModal').classList.add('flex');
    }

    hideLoginModal() {
        document.getElementById('loginModal').classList.add('hidden');
        document.getElementById('loginModal').classList.remove('flex');
        this.resetLoginForm();
    }

    showRegisterModal() {
        document.getElementById('registerModal').classList.remove('hidden');
        document.getElementById('registerModal').classList.add('flex');
    }

    hideRegisterModal() {
        document.getElementById('registerModal').classList.add('hidden');
        document.getElementById('registerModal').classList.remove('flex');
        this.resetRegisterForm();
    }

    showDepositModal() {
        this.generateDepositAddress();
        document.getElementById('depositModal').classList.remove('hidden');
        document.getElementById('depositModal').classList.add('flex');
    }

    hideDepositModal() {
        document.getElementById('depositModal').classList.add('hidden');
        document.getElementById('depositModal').classList.remove('flex');
    }

    showWithdrawModal() {
        document.getElementById('withdrawModal').classList.remove('hidden');
        document.getElementById('withdrawModal').classList.add('flex');
    }

    hideWithdrawModal() {
        document.getElementById('withdrawModal').classList.add('hidden');
        document.getElementById('withdrawModal').classList.remove('flex');
        this.resetWithdrawForm();
    }

    // Authentication functions
    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        this.setLoginLoading(true);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentUser = data;
                this.isAuthenticated = true;
                this.updateUserInterface();
                this.hideLoginModal();
                this.showToast('Login successful!', 'success');
                this.showAppropriateScreen();
            } else {
                this.showToast(data.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast('Login failed. Please try again.', 'error');
        }
        
        this.setLoginLoading(false);
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        this.setRegisterLoading(true);
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.hideRegisterModal();
                this.showToast('Registration successful! Please login.', 'success');
                this.showLoginModal();
            } else {
                this.showToast(data.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Register error:', error);
            this.showToast('Registration failed. Please try again.', 'error');
        }
        
        this.setRegisterLoading(false);
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            this.currentUser = null;
            this.isAuthenticated = false;
            this.updateUserInterface();
            this.showWelcomeScreen();
            this.showToast('Logged out successfully', 'success');
            
            // Disconnect WebSocket
            if (this.socket) {
                this.socket.disconnect();
                this.socket = null;
            }
        } catch (error) {
            console.error('Logout error:', error);
            this.showToast('Logout failed', 'error');
        }
    }

    // Player dashboard functions
    async loadPlayerData() {
        try {
            const response = await fetch('/api/player/balance', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                document.getElementById('btcBalance').textContent = data.btc_balance.toFixed(8);
                document.getElementById('usdEquivalent').textContent = `$${data.usd_equivalent.toFixed(2)} USD`;
                document.getElementById('walletAddress').textContent = data.wallet_address;
            }
        } catch (error) {
            console.error('Error loading player data:', error);
        }
        
        // Load transaction history
        this.loadTransactionHistory();
    }

    async loadTransactionHistory() {
        try {
            const response = await fetch('/api/player/transactions?limit=10', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderTransactionHistory(data.transactions);
            }
        } catch (error) {
            console.error('Error loading transaction history:', error);
        }
    }

    renderTransactionHistory(transactions) {
        const tbody = document.getElementById('transactionHistory');
        
        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-gray-400">No transactions found</td></tr>';
            return;
        }
        
        tbody.innerHTML = transactions.map(tx => `
            <tr class="border-b border-gray-700">
                <td class="py-2">
                    <span class="px-2 py-1 rounded text-xs ${tx.type === 'deposit' ? 'bg-green-600' : 'bg-orange-600'}">
                        ${tx.type.toUpperCase()}
                    </span>
                </td>
                <td class="py-2">${tx.amount} BTC</td>
                <td class="py-2">
                    <span class="px-2 py-1 rounded text-xs ${this.getStatusColor(tx.status)}">
                        ${tx.status.toUpperCase()}
                    </span>
                </td>
                <td class="py-2">${new Date(tx.created_at).toLocaleDateString()}</td>
                <td class="py-2">
                    <button onclick="app.viewTransactionDetails('${tx.id}')" class="text-blue-400 hover:text-blue-300 text-xs">
                        View
                    </button>
                </td>
            </tr>
        `).join('');
    }

    getStatusColor(status) {
        const colors = {
            'completed': 'bg-green-600',
            'pending': 'bg-yellow-600',
            'failed': 'bg-red-600',
            'rejected': 'bg-red-600',
            'flagged': 'bg-purple-600',
            'initiated': 'bg-blue-600',
            'broadcasting': 'bg-blue-600'
        };
        return colors[status] || 'bg-gray-600';
    }

    async generateDepositAddress() {
        try {
            const response = await fetch('/api/player/deposit/address', {
                method: 'POST',
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                document.getElementById('depositAddress').textContent = data.deposit_address;
                document.getElementById('qrCode').innerHTML = `<img src="${data.qr_code_url}" alt="QR Code" class="max-w-xs">`;
            }
        } catch (error) {
            console.error('Error generating deposit address:', error);
        }
    }

    async handleWithdraw(e) {
        e.preventDefault();
        
        const toAddress = document.getElementById('withdrawAddress').value;
        const amount = parseFloat(document.getElementById('withdrawAmount').value);
        
        this.setWithdrawLoading(true);
        
        try {
            const response = await fetch('/api/player/withdraw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ to_address: toAddress, amount })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.hideWithdrawModal();
                this.showToast('Withdrawal request submitted!', 'success');
                this.refreshPlayerData();
            } else {
                this.showToast(data.message || 'Withdrawal failed', 'error');
            }
        } catch (error) {
            console.error('Withdraw error:', error);
            this.showToast('Withdrawal failed. Please try again.', 'error');
        }
        
        this.setWithdrawLoading(false);
    }

    async simulateDeposit() {
        try {
            const response = await fetch('/api/player/simulate_deposit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ amount: 0.1 })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast('Deposit simulation started! Check your transaction history.', 'success');
                setTimeout(() => this.refreshPlayerData(), 2000);
            } else {
                this.showToast(data.message || 'Simulation failed', 'error');
            }
        } catch (error) {
            console.error('Simulate deposit error:', error);
            this.showToast('Simulation failed', 'error');
        }
    }

    async refreshPlayerData() {
        this.loadPlayerData();
        this.showToast('Data refreshed', 'success');
    }

    copyWalletAddress() {
        const address = document.getElementById('walletAddress').textContent;
        navigator.clipboard.writeText(address).then(() => {
            this.showToast('Address copied to clipboard!', 'success');
        });
    }



    // Utility functions
    setLoginLoading(loading) {
        const btnText = document.getElementById('loginBtnText');
        const spinner = document.getElementById('loginSpinner');
        
        if (loading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    }

    setRegisterLoading(loading) {
        const btnText = document.getElementById('registerBtnText');
        const spinner = document.getElementById('registerSpinner');
        
        if (loading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    }

    setWithdrawLoading(loading) {
        const btnText = document.getElementById('withdrawBtnText');
        const spinner = document.getElementById('withdrawSpinner');
        
        if (loading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    }

    resetLoginForm() {
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
    }

    resetRegisterForm() {
        document.getElementById('registerUsername').value = '';
        document.getElementById('registerEmail').value = '';
        document.getElementById('registerPassword').value = '';
    }

    resetWithdrawForm() {
        document.getElementById('withdrawAddress').value = '';
        document.getElementById('withdrawAmount').value = '';
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const icon = document.getElementById('toastIcon');
        const messageEl = document.getElementById('toastMessage');
        
        const icons = {
            success: '<i class="fas fa-check-circle text-green-400"></i>',
            error: '<i class="fas fa-exclamation-circle text-red-400"></i>',
            warning: '<i class="fas fa-exclamation-triangle text-yellow-400"></i>',
            info: '<i class="fas fa-info-circle text-blue-400"></i>'
        };
        
        icon.innerHTML = icons[type] || icons.info;
        messageEl.textContent = message;
        
        // Show toast
        toast.classList.remove('translate-x-full');
        
        // Hide after 3 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
        }, 3000);
    }

    async viewTransactionDetails(txId) {
        try {
            const response = await fetch(`/api/player/transaction/${txId}/status`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                alert(`Transaction Details:\nID: ${data.transaction_id}\nStatus: ${data.status}\nConfirmations: ${data.confirmations}\nAmount: ${data.amount} BTC`);
            }
        } catch (error) {
            console.error('Error viewing transaction details:', error);
        }
    }

    // WebSocket functions
    initializeWebSocket() {
        if (this.isAuthenticated) {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.socket.emit('join', { user_id: this.currentUser.id, role: this.currentUser.role });
            });
            
            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
            });
            
            this.socket.on('transaction_update', (data) => {
                this.handleTransactionUpdate(data);
            });
            
            this.socket.on('risk_alert', (data) => {
                this.handleRiskAlert(data);
            });
            
            this.socket.on('compliance_report', (data) => {
                this.handleComplianceReport(data);
            });
        }
    }

    handleTransactionUpdate(data) {
        this.showToast(`Transaction ${data.transaction_id} updated to ${data.status}`, 'info');
        if (this.isAuthenticated && this.currentUser.role === 'player') {
            this.refreshPlayerData();
        }
    }

    handleRiskAlert(data) {
        this.showToast(`Risk Alert: ${data.message}`, 'warning');
    }

    handleComplianceReport(data) {
        this.showToast(`Compliance Report: ${data.message}`, 'info');
    }
}

// Initialize the application
const app = new ChainGateApp();

