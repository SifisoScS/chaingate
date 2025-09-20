// ChainGate Dashboard JavaScript
class Dashboard {
    constructor() {
        this.refreshInterval = null;
        this.charts = {};
    }

    // Player Dashboard Functions
    async initPlayerDashboard() {
        await this.loadPlayerBalance();
        await this.loadPlayerTransactions();
        this.startAutoRefresh();
    }

    async loadPlayerBalance() {
        try {
            const response = await fetch('/api/player/balance', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateBalanceDisplay(data);
            }
        } catch (error) {
            console.error('Error loading balance:', error);
        }
    }

    updateBalanceDisplay(data) {
        document.getElementById('btcBalance').textContent = data.btc_balance.toFixed(8);
        document.getElementById('usdEquivalent').textContent = `$${data.usd_equivalent.toFixed(2)} USD`;
        document.getElementById('walletAddress').textContent = data.wallet_address;
        
        // Add animation to balance update
        const balanceEl = document.getElementById('btcBalance');
        balanceEl.classList.add('animate-pulseGlow');
        setTimeout(() => {
            balanceEl.classList.remove('animate-pulseGlow');
        }, 2000);
    }

    async loadPlayerTransactions(page = 1, filter = 'all') {
        try {
            const response = await fetch(`/api/player/transactions?page=${page}&filter=${filter}&limit=20`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderTransactionTable(data.transactions);
                this.renderPagination(data.current_page, data.total_pages);
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
        }
    }

    renderTransactionTable(transactions) {
        const tbody = document.getElementById('transactionHistory');
        
        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-8 text-gray-400">
                        <i class="fas fa-inbox text-4xl mb-4"></i>
                        <p>No transactions found</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = transactions.map(tx => `
            <tr class="border-b border-gray-700 hover:bg-gray-800/50 transition-colors animate-fadeIn">
                <td class="py-3">
                    <div class="flex items-center space-x-2">
                        <i class="fas ${tx.type === 'deposit' ? 'fa-arrow-down text-green-400' : 'fa-arrow-up text-orange-400'}"></i>
                        <span class="px-2 py-1 rounded text-xs font-medium ${tx.type === 'deposit' ? 'bg-green-600/20 text-green-400' : 'bg-orange-600/20 text-orange-400'}">
                            ${tx.type.toUpperCase()}
                        </span>
                    </div>
                </td>
                <td class="py-3">
                    <div class="font-mono">${parseFloat(tx.amount).toFixed(8)} BTC</div>
                    ${tx.fee > 0 ? `<div class="text-xs text-gray-400">Fee: ${parseFloat(tx.fee).toFixed(8)} BTC</div>` : ''}
                </td>
                <td class="py-3">
                    <span class="px-2 py-1 rounded text-xs font-medium ${this.getStatusStyle(tx.status)}">
                        ${this.getStatusText(tx.status)}
                    </span>
                    ${tx.confirmations > 0 ? `<div class="text-xs text-gray-400 mt-1">${tx.confirmations} confirmations</div>` : ''}
                </td>
                <td class="py-3">
                    <div>${new Date(tx.created_at).toLocaleDateString()}</div>
                    <div class="text-xs text-gray-400">${new Date(tx.created_at).toLocaleTimeString()}</div>
                </td>
                <td class="py-3">
                    <div class="flex space-x-2">
                        <button onclick="dashboard.viewTransactionDetails('${tx.id}')" class="text-blue-400 hover:text-blue-300 text-xs transition-colors">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                        ${tx.tx_hash ? `<button onclick="dashboard.viewOnExplorer('${tx.tx_hash}')" class="text-purple-400 hover:text-purple-300 text-xs transition-colors">
                            <i class="fas fa-external-link-alt mr-1"></i>Explorer
                        </button>` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    getStatusStyle(status) {
        const styles = {
            'completed': 'bg-green-600/20 text-green-400',
            'pending': 'bg-yellow-600/20 text-yellow-400',
            'pending_admin': 'bg-blue-600/20 text-blue-400',
            'failed': 'bg-red-600/20 text-red-400',
            'rejected': 'bg-red-600/20 text-red-400',
            'flagged': 'bg-purple-600/20 text-purple-400',
            'initiated': 'bg-blue-600/20 text-blue-400',
            'broadcasting': 'bg-indigo-600/20 text-indigo-400',
            'approved': 'bg-green-600/20 text-green-400'
        };
        return styles[status] || 'bg-gray-600/20 text-gray-400';
    }

    getStatusText(status) {
        const texts = {
            'pending_admin': 'PENDING APPROVAL',
            'broadcasting': 'BROADCASTING'
        };
        return texts[status] || status.toUpperCase();
    }

    renderPagination(currentPage, totalPages) {
        if (totalPages <= 1) return;
        
        // Implementation for pagination controls
        // This would add pagination buttons below the transaction table
    }

    async viewTransactionDetails(txId) {
        try {
            const response = await fetch(`/api/player/transaction/${txId}/status`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showTransactionModal(data);
            }
        } catch (error) {
            console.error('Error viewing transaction details:', error);
            app.showToast('Failed to load transaction details', 'error');
        }
    }

    showTransactionModal(txData) {
        // Create and show a detailed transaction modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="glass-dark p-8 rounded-xl max-w-md w-full mx-4 animate-fadeIn">
                <h3 class="text-2xl font-bold mb-6">Transaction Details</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Transaction ID</label>
                        <div class="font-mono text-sm break-all">${txData.transaction_id}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Type</label>
                        <div class="capitalize">${txData.type}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Amount</label>
                        <div class="font-mono">${txData.amount} BTC</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Status</label>
                        <div class="capitalize">${txData.status}</div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Confirmations</label>
                        <div>${txData.confirmations}</div>
                    </div>
                    ${txData.tx_hash ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-400">Transaction Hash</label>
                        <div class="font-mono text-sm break-all">${txData.tx_hash}</div>
                    </div>
                    ` : ''}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="gradient-primary w-full py-2 rounded-lg hover:opacity-90 transition-opacity mt-6">
                    Close
                </button>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    viewOnExplorer(txHash) {
        // Mock blockchain explorer
        app.showToast(`Mock Explorer: ${txHash}`, 'info');
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadPlayerBalance();
            this.loadPlayerTransactions();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Admin Dashboard Functions
    async initAdminDashboard() {
        await this.loadAdminStats();
        await this.loadAdminTransactions();
        this.createAdminCharts();
    }

    async loadAdminStats() {
        try {
            const response = await fetch('/api/admin/dashboard/stats', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderAdminStats(data.stats);
            }
        } catch (error) {
            console.error('Error loading admin stats:', error);
        }
    }

    renderAdminStats(stats) {
        const container = document.getElementById('adminStats');
        container.innerHTML = `
            <div class="glass-dark p-6 rounded-xl animate-fadeIn">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Total Users</h3>
                    <i class="fas fa-users text-blue-400 text-2xl"></i>
                </div>
                <div class="text-3xl font-bold text-blue-400 mb-2">${stats.users.total}</div>
                <div class="text-sm text-gray-400">${stats.users.active} active, ${stats.users.inactive} inactive</div>
            </div>
            <div class="glass-dark p-6 rounded-xl animate-fadeIn">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Pending Reviews</h3>
                    <i class="fas fa-clock text-yellow-400 text-2xl"></i>
                </div>
                <div class="text-3xl font-bold text-yellow-400 mb-2">${stats.transactions.pending}</div>
                <div class="text-sm text-gray-400">Require admin action</div>
            </div>
            <div class="glass-dark p-6 rounded-xl animate-fadeIn">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Flagged Items</h3>
                    <i class="fas fa-flag text-red-400 text-2xl"></i>
                </div>
                <div class="text-3xl font-bold text-red-400 mb-2">${stats.transactions.flagged}</div>
                <div class="text-sm text-gray-400">Need investigation</div>
            </div>
            <div class="glass-dark p-6 rounded-xl animate-fadeIn">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Today's Activity</h3>
                    <i class="fas fa-chart-line text-green-400 text-2xl"></i>
                </div>
                <div class="text-3xl font-bold text-green-400 mb-2">${stats.transactions.today}</div>
                <div class="text-sm text-gray-400">New transactions</div>
            </div>
        `;
    }

    async loadAdminTransactions() {
        try {
            const response = await fetch('/api/admin/transactions?status=pending&limit=10', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.renderAdminTransactionList(data.transactions);
            }
        } catch (error) {
            console.error('Error loading admin transactions:', error);
        }
    }

    renderAdminTransactionList(transactions) {
        const content = document.getElementById('adminContent');
        
        if (transactions.length === 0) {
            content.innerHTML = `
                <div class="text-center py-12">
                    <i class="fas fa-check-circle text-6xl text-green-400 mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">All Caught Up!</h3>
                    <p class="text-gray-400">No pending transactions require review</p>
                </div>
            `;
            return;
        }
        
        content.innerHTML = `
            <h3 class="text-xl font-semibold mb-6">Pending Transactions</h3>
            <div class="space-y-4">
                ${transactions.map(tx => `
                    <div class="glass p-4 rounded-lg animate-fadeIn">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <div class="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                                    <i class="fas ${tx.type === 'deposit' ? 'fa-arrow-down' : 'fa-arrow-up'} text-white"></i>
                                </div>
                                <div>
                                    <div class="font-semibold">${tx.user ? tx.user.username : 'Unknown User'}</div>
                                    <div class="text-sm text-gray-400">${tx.type.toUpperCase()} • ${parseFloat(tx.amount).toFixed(8)} BTC</div>
                                    <div class="text-xs text-gray-500">${new Date(tx.created_at).toLocaleString()}</div>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                <button onclick="dashboard.approveTransaction('${tx.id}')" class="gradient-success px-4 py-2 rounded-lg text-sm hover:opacity-90 transition-opacity">
                                    <i class="fas fa-check mr-1"></i>Approve
                                </button>
                                <button onclick="dashboard.rejectTransaction('${tx.id}')" class="gradient-danger px-4 py-2 rounded-lg text-sm hover:opacity-90 transition-opacity">
                                    <i class="fas fa-times mr-1"></i>Reject
                                </button>
                                <button onclick="dashboard.flagTransaction('${tx.id}')" class="gradient-warning px-4 py-2 rounded-lg text-sm hover:opacity-90 transition-opacity">
                                    <i class="fas fa-flag mr-1"></i>Flag
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async approveTransaction(txId) {
        if (!confirm('Are you sure you want to approve this transaction?')) return;
        
        try {
            const response = await fetch(`/api/admin/transactions/${txId}/approve`, {
                method: 'POST',
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                app.showToast('Transaction approved successfully', 'success');
                this.loadAdminTransactions();
                this.loadAdminStats();
            } else {
                app.showToast(data.message || 'Failed to approve transaction', 'error');
            }
        } catch (error) {
            console.error('Error approving transaction:', error);
            app.showToast('Failed to approve transaction', 'error');
        }
    }

    async rejectTransaction(txId) {
        const reason = prompt('Please provide a reason for rejection:');
        if (!reason) return;
        
        try {
            const response = await fetch(`/api/admin/transactions/${txId}/reject`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ reason })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                app.showToast('Transaction rejected successfully', 'success');
                this.loadAdminTransactions();
                this.loadAdminStats();
            } else {
                app.showToast(data.message || 'Failed to reject transaction', 'error');
            }
        } catch (error) {
            console.error('Error rejecting transaction:', error);
            app.showToast('Failed to reject transaction', 'error');
        }
    }

    async flagTransaction(txId) {
        const reason = prompt('Please provide a reason for flagging:');
        if (!reason) return;
        
        try {
            const response = await fetch(`/api/admin/transactions/${txId}/flag`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ reason })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                app.showToast('Transaction flagged successfully', 'success');
                this.loadAdminTransactions();
                this.loadAdminStats();
            } else {
                app.showToast(data.message || 'Failed to flag transaction', 'error');
            }
        } catch (error) {
            console.error('Error flagging transaction:', error);
            app.showToast('Failed to flag transaction', 'error');
        }
    }

    createAdminCharts() {
        // This would create Chart.js charts for admin analytics
        // Implementation would go here for transaction volume charts, etc.
    }

    // Utility Functions
    formatCurrency(amount, currency = 'BTC') {
        if (currency === 'BTC') {
            return `${parseFloat(amount).toFixed(8)} BTC`;
        } else if (currency === 'USD') {
            return `$${parseFloat(amount).toFixed(2)}`;
        }
        return `${amount} ${currency}`;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return {
            date: date.toLocaleDateString(),
            time: date.toLocaleTimeString(),
            relative: this.getRelativeTime(date)
        };
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
}

// Initialize dashboard
const dashboard = new Dashboard();

