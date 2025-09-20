// ChainGate Transactions JavaScript
class TransactionManager {
    constructor() {
        this.pollingIntervals = new Map();
        this.transactionCache = new Map();
    }

    // Transaction Status Polling
    startPolling(transactionId, callback, interval = 5000) {
        if (this.pollingIntervals.has(transactionId)) {
            this.stopPolling(transactionId);
        }

        const pollInterval = setInterval(async () => {
            try {
                const status = await this.getTransactionStatus(transactionId);
                callback(status);
                
                // Stop polling if transaction is in final state
                if (this.isFinalState(status.status)) {
                    this.stopPolling(transactionId);
                }
            } catch (error) {
                console.error('Error polling transaction status:', error);
                this.stopPolling(transactionId);
            }
        }, interval);

        this.pollingIntervals.set(transactionId, pollInterval);
    }

    stopPolling(transactionId) {
        const interval = this.pollingIntervals.get(transactionId);
        if (interval) {
            clearInterval(interval);
            this.pollingIntervals.delete(transactionId);
        }
    }

    stopAllPolling() {
        this.pollingIntervals.forEach((interval, txId) => {
            clearInterval(interval);
        });
        this.pollingIntervals.clear();
    }

    isFinalState(status) {
        const finalStates = ['completed', 'failed', 'rejected'];
        return finalStates.includes(status);
    }

    async getTransactionStatus(transactionId) {
        try {
            const response = await fetch(`/api/player/transaction/${transactionId}/status`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.transactionCache.set(transactionId, data);
                return data;
            }
            throw new Error(data.message || 'Failed to get transaction status');
        } catch (error) {
            console.error('Error getting transaction status:', error);
            throw error;
        }
    }

    // Transaction History Management
    async loadTransactionHistory(filters = {}) {
        const params = new URLSearchParams();
        
        if (filters.type && filters.type !== 'all') {
            params.append('filter', filters.type);
        }
        if (filters.dateRange && filters.dateRange !== 'all') {
            params.append('date_range', filters.dateRange);
        }
        if (filters.page) {
            params.append('page', filters.page);
        }
        if (filters.limit) {
            params.append('limit', filters.limit);
        }

        try {
            const response = await fetch(`/api/player/transactions?${params}`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                return data;
            }
            throw new Error(data.message || 'Failed to load transaction history');
        } catch (error) {
            console.error('Error loading transaction history:', error);
            throw error;
        }
    }

    // Transaction Creation and Management
    async createWithdrawal(toAddress, amount) {
        try {
            const response = await fetch('/api/player/withdraw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    to_address: toAddress,
                    amount: parseFloat(amount)
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Start polling for this transaction
                this.startPolling(data.transaction_id, (status) => {
                    this.updateTransactionInUI(status);
                });
                
                return data;
            }
            throw new Error(data.message || 'Failed to create withdrawal');
        } catch (error) {
            console.error('Error creating withdrawal:', error);
            throw error;
        }
    }

    async simulateDeposit(amount = 0.1) {
        try {
            const response = await fetch('/api/player/simulate_deposit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ amount })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Start polling for this transaction
                this.startPolling(data.transaction_id, (status) => {
                    this.updateTransactionInUI(status);
                    this.showTransactionProgress(status);
                });
                
                return data;
            }
            throw new Error(data.message || 'Failed to simulate deposit');
        } catch (error) {
            console.error('Error simulating deposit:', error);
            throw error;
        }
    }

    // UI Update Functions
    updateTransactionInUI(transactionData) {
        const txRow = document.querySelector(`[data-tx-id="${transactionData.transaction_id}"]`);
        if (txRow) {
            // Update status cell
            const statusCell = txRow.querySelector('.tx-status');
            if (statusCell) {
                statusCell.innerHTML = `
                    <span class="px-2 py-1 rounded text-xs font-medium ${dashboard.getStatusStyle(transactionData.status)}">
                        ${dashboard.getStatusText(transactionData.status)}
                    </span>
                    ${transactionData.confirmations > 0 ? `<div class="text-xs text-gray-400 mt-1">${transactionData.confirmations} confirmations</div>` : ''}
                `;
            }
        }
        
        // Update balance if transaction completed
        if (transactionData.status === 'completed') {
            app.loadPlayerData();
            app.showToast(`Transaction completed: ${transactionData.amount} BTC`, 'success');
        }
    }

    showTransactionProgress(transactionData) {
        const progressToast = this.createProgressToast(transactionData);
        document.body.appendChild(progressToast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (progressToast.parentNode) {
                progressToast.remove();
            }
        }, 5000);
    }

    createProgressToast(transactionData) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-6 right-6 glass-dark p-4 rounded-lg shadow-lg max-w-sm animate-slideInRight z-50';
        
        const progressPercentage = this.calculateProgress(transactionData.status, transactionData.confirmations);
        
        toast.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="fas ${transactionData.type === 'deposit' ? 'fa-arrow-down text-green-400' : 'fa-arrow-up text-orange-400'} text-xl"></i>
                </div>
                <div class="flex-1">
                    <h4 class="font-semibold text-sm">${transactionData.type === 'deposit' ? 'Deposit' : 'Withdrawal'} Progress</h4>
                    <p class="text-xs text-gray-400 mb-2">${transactionData.amount} BTC</p>
                    <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
                        <div class="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500" style="width: ${progressPercentage}%"></div>
                    </div>
                    <p class="text-xs text-gray-300">${this.getProgressText(transactionData.status, transactionData.confirmations)}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-white">
                    <i class="fas fa-times text-sm"></i>
                </button>
            </div>
        `;
        
        return toast;
    }

    calculateProgress(status, confirmations) {
        const progressMap = {
            'initiated': 10,
            'broadcasting': 25,
            'pending': 50 + (confirmations * 15), // 50% + 15% per confirmation
            'completed': 100,
            'failed': 0,
            'rejected': 0
        };
        
        return Math.min(progressMap[status] || 0, 100);
    }

    getProgressText(status, confirmations) {
        const textMap = {
            'initiated': 'Transaction initiated...',
            'broadcasting': 'Broadcasting to network...',
            'pending': `Confirming... (${confirmations}/3)`,
            'completed': 'Transaction completed!',
            'failed': 'Transaction failed',
            'rejected': 'Transaction rejected'
        };
        
        return textMap[status] || 'Processing...';
    }

    // Transaction Validation
    validateBitcoinAddress(address) {
        // Basic Bitcoin address validation
        const patterns = {
            legacy: /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$/,
            segwit: /^bc1[a-z0-9]{39,59}$/,
            testnet: /^[2mn][a-km-zA-HJ-NP-Z1-9]{25,34}$/
        };
        
        return Object.values(patterns).some(pattern => pattern.test(address));
    }

    validateAmount(amount, maxAmount) {
        const numAmount = parseFloat(amount);
        
        if (isNaN(numAmount) || numAmount <= 0) {
            return { valid: false, message: 'Amount must be a positive number' };
        }
        
        if (numAmount < 0.00000001) {
            return { valid: false, message: 'Amount must be at least 0.00000001 BTC' };
        }
        
        if (maxAmount && numAmount > maxAmount) {
            return { valid: false, message: `Amount cannot exceed ${maxAmount} BTC` };
        }
        
        return { valid: true };
    }

    // Transaction Filtering and Sorting
    filterTransactions(transactions, filters) {
        let filtered = [...transactions];
        
        if (filters.type && filters.type !== 'all') {
            filtered = filtered.filter(tx => tx.type === filters.type);
        }
        
        if (filters.status && filters.status !== 'all') {
            filtered = filtered.filter(tx => tx.status === filters.status);
        }
        
        if (filters.dateFrom) {
            const fromDate = new Date(filters.dateFrom);
            filtered = filtered.filter(tx => new Date(tx.created_at) >= fromDate);
        }
        
        if (filters.dateTo) {
            const toDate = new Date(filters.dateTo);
            filtered = filtered.filter(tx => new Date(tx.created_at) <= toDate);
        }
        
        if (filters.amountMin) {
            filtered = filtered.filter(tx => parseFloat(tx.amount) >= parseFloat(filters.amountMin));
        }
        
        if (filters.amountMax) {
            filtered = filtered.filter(tx => parseFloat(tx.amount) <= parseFloat(filters.amountMax));
        }
        
        return filtered;
    }

    sortTransactions(transactions, sortBy, sortOrder = 'desc') {
        return transactions.sort((a, b) => {
            let aVal, bVal;
            
            switch (sortBy) {
                case 'date':
                    aVal = new Date(a.created_at);
                    bVal = new Date(b.created_at);
                    break;
                case 'amount':
                    aVal = parseFloat(a.amount);
                    bVal = parseFloat(b.amount);
                    break;
                case 'type':
                    aVal = a.type;
                    bVal = b.type;
                    break;
                case 'status':
                    aVal = a.status;
                    bVal = b.status;
                    break;
                default:
                    return 0;
            }
            
            if (sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    // Export Functions
    async exportTransactions(format = 'csv', filters = {}) {
        try {
            const transactions = await this.loadTransactionHistory(filters);
            
            if (format === 'csv') {
                this.exportToCSV(transactions.transactions);
            } else if (format === 'json') {
                this.exportToJSON(transactions.transactions);
            }
        } catch (error) {
            console.error('Error exporting transactions:', error);
            app.showToast('Failed to export transactions', 'error');
        }
    }

    exportToCSV(transactions) {
        const headers = ['Date', 'Type', 'Amount (BTC)', 'Status', 'Confirmations', 'Transaction Hash'];
        const csvContent = [
            headers.join(','),
            ...transactions.map(tx => [
                new Date(tx.created_at).toISOString(),
                tx.type,
                tx.amount,
                tx.status,
                tx.confirmations || 0,
                tx.tx_hash || ''
            ].join(','))
        ].join('\n');
        
        this.downloadFile(csvContent, 'transactions.csv', 'text/csv');
    }

    exportToJSON(transactions) {
        const jsonContent = JSON.stringify(transactions, null, 2);
        this.downloadFile(jsonContent, 'transactions.json', 'application/json');
    }

    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // Cleanup
    destroy() {
        this.stopAllPolling();
        this.transactionCache.clear();
    }
}

// Initialize transaction manager
const transactionManager = new TransactionManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    transactionManager.destroy();
});

