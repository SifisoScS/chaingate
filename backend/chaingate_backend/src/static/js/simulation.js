// ChainGate Simulation JavaScript
class BitcoinSimulation {
    constructor() {
        this.simulationSettings = {
            confirmationDelay: 30000, // 30 seconds between confirmations in demo
            maxConfirmations: 3,
            failureRate: 0.05, // 5% chance of failure
            withdrawalDelay: 60000 // 1 minute delay for withdrawals
        };
        
        this.activeSimulations = new Map();
        this.networkStats = {
            totalTransactions: 0,
            successfulTransactions: 0,
            failedTransactions: 0,
            averageConfirmationTime: 0
        };
    }

    // Deposit Simulation
    async startDepositSimulation(amount = 0.1) {
        try {
            app.showToast('Starting deposit simulation...', 'info');
            
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
                this.trackSimulation(data.transaction_id, 'deposit', amount);
                this.showSimulationProgress(data.transaction_id, 'deposit', amount);
                
                // Start monitoring this transaction
                transactionManager.startPolling(data.transaction_id, (status) => {
                    this.updateSimulationProgress(data.transaction_id, status);
                });
                
                return data;
            } else {
                throw new Error(data.message || 'Simulation failed');
            }
        } catch (error) {
            console.error('Deposit simulation error:', error);
            app.showToast('Deposit simulation failed', 'error');
            throw error;
        }
    }

    // Withdrawal Simulation
    async startWithdrawalSimulation(toAddress, amount) {
        try {
            // Validate inputs
            if (!transactionManager.validateBitcoinAddress(toAddress)) {
                throw new Error('Invalid Bitcoin address');
            }
            
            const amountValidation = transactionManager.validateAmount(amount);
            if (!amountValidation.valid) {
                throw new Error(amountValidation.message);
            }
            
            app.showToast('Starting withdrawal simulation...', 'info');
            
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
                this.trackSimulation(data.transaction_id, 'withdrawal', amount);
                this.showSimulationProgress(data.transaction_id, 'withdrawal', amount);
                
                // Start monitoring this transaction
                transactionManager.startPolling(data.transaction_id, (status) => {
                    this.updateSimulationProgress(data.transaction_id, status);
                });
                
                return data;
            } else {
                throw new Error(data.message || 'Withdrawal failed');
            }
        } catch (error) {
            console.error('Withdrawal simulation error:', error);
            app.showToast(error.message || 'Withdrawal simulation failed', 'error');
            throw error;
        }
    }

    // Simulation Tracking
    trackSimulation(transactionId, type, amount) {
        this.activeSimulations.set(transactionId, {
            id: transactionId,
            type,
            amount,
            startTime: Date.now(),
            status: 'initiated',
            confirmations: 0
        });
        
        this.networkStats.totalTransactions++;
        this.updateNetworkStatsDisplay();
    }

    updateSimulationProgress(transactionId, statusData) {
        const simulation = this.activeSimulations.get(transactionId);
        if (!simulation) return;
        
        simulation.status = statusData.status;
        simulation.confirmations = statusData.confirmations || 0;
        
        // Update progress display
        this.updateProgressDisplay(transactionId, simulation, statusData);
        
        // Handle completion
        if (transactionManager.isFinalState(statusData.status)) {
            this.completeSimulation(transactionId, statusData.status);
        }
    }

    completeSimulation(transactionId, finalStatus) {
        const simulation = this.activeSimulations.get(transactionId);
        if (!simulation) return;
        
        const duration = Date.now() - simulation.startTime;
        
        if (finalStatus === 'completed') {
            this.networkStats.successfulTransactions++;
            this.showCompletionCelebration(simulation);
        } else {
            this.networkStats.failedTransactions++;
        }
        
        // Update average confirmation time
        this.updateAverageConfirmationTime(duration);
        
        // Clean up
        this.activeSimulations.delete(transactionId);
        this.updateNetworkStatsDisplay();
        
        // Remove progress display after a delay
        setTimeout(() => {
            this.removeProgressDisplay(transactionId);
        }, 5000);
    }

    // Progress Display Functions
    showSimulationProgress(transactionId, type, amount) {
        const progressContainer = this.getOrCreateProgressContainer();
        
        const progressElement = document.createElement('div');
        progressElement.id = `simulation-${transactionId}`;
        progressElement.className = 'glass p-4 rounded-lg mb-4 animate-fadeIn';
        
        progressElement.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-r ${type === 'deposit' ? 'from-green-500 to-emerald-600' : 'from-orange-500 to-amber-600'} flex items-center justify-center">
                        <i class="fas ${type === 'deposit' ? 'fa-arrow-down' : 'fa-arrow-up'} text-white"></i>
                    </div>
                    <div>
                        <h4 class="font-semibold">${type === 'deposit' ? 'Deposit' : 'Withdrawal'} Simulation</h4>
                        <p class="text-sm text-gray-400">${amount} BTC</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm font-medium" id="status-${transactionId}">Initiated</div>
                    <div class="text-xs text-gray-400" id="confirmations-${transactionId}">0 confirmations</div>
                </div>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div id="progress-${transactionId}" class="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000" style="width: 10%"></div>
            </div>
            <div class="flex justify-between text-xs text-gray-400">
                <span id="progress-text-${transactionId}">Starting simulation...</span>
                <span id="time-${transactionId}">0s</span>
            </div>
        `;
        
        progressContainer.appendChild(progressElement);
        
        // Start time counter
        this.startTimeCounter(transactionId);
    }

    updateProgressDisplay(transactionId, simulation, statusData) {
        const statusEl = document.getElementById(`status-${transactionId}`);
        const confirmationsEl = document.getElementById(`confirmations-${transactionId}`);
        const progressEl = document.getElementById(`progress-${transactionId}`);
        const progressTextEl = document.getElementById(`progress-text-${transactionId}`);
        
        if (!statusEl) return;
        
        // Update status
        statusEl.textContent = this.getStatusDisplayText(statusData.status);
        statusEl.className = `text-sm font-medium ${this.getStatusColor(statusData.status)}`;
        
        // Update confirmations
        if (confirmationsEl) {
            confirmationsEl.textContent = `${statusData.confirmations || 0} confirmations`;
        }
        
        // Update progress bar
        if (progressEl) {
            const progress = transactionManager.calculateProgress(statusData.status, statusData.confirmations);
            progressEl.style.width = `${progress}%`;
        }
        
        // Update progress text
        if (progressTextEl) {
            progressTextEl.textContent = transactionManager.getProgressText(statusData.status, statusData.confirmations);
        }
    }

    removeProgressDisplay(transactionId) {
        const element = document.getElementById(`simulation-${transactionId}`);
        if (element) {
            element.classList.add('animate-fadeOut');
            setTimeout(() => {
                element.remove();
            }, 500);
        }
    }

    getOrCreateProgressContainer() {
        let container = document.getElementById('simulation-progress-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'simulation-progress-container';
            container.className = 'fixed bottom-6 left-6 max-w-md z-40';
            document.body.appendChild(container);
        }
        return container;
    }

    startTimeCounter(transactionId) {
        const startTime = Date.now();
        const timeEl = document.getElementById(`time-${transactionId}`);
        
        const updateTime = () => {
            if (timeEl && this.activeSimulations.has(transactionId)) {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                timeEl.textContent = `${elapsed}s`;
                setTimeout(updateTime, 1000);
            }
        };
        
        updateTime();
    }

    // Completion Celebration
    showCompletionCelebration(simulation) {
        const celebration = document.createElement('div');
        celebration.className = 'fixed inset-0 pointer-events-none z-50 flex items-center justify-center';
        
        celebration.innerHTML = `
            <div class="glass-dark p-8 rounded-xl text-center animate-fadeIn">
                <div class="text-6xl mb-4">🎉</div>
                <h3 class="text-2xl font-bold mb-2">Transaction Completed!</h3>
                <p class="text-gray-300">${simulation.amount} BTC ${simulation.type}</p>
                <div class="mt-4">
                    <i class="fas fa-check-circle text-green-400 text-3xl"></i>
                </div>
            </div>
        `;
        
        document.body.appendChild(celebration);
        
        // Add confetti effect
        this.createConfetti();
        
        // Remove after 3 seconds
        setTimeout(() => {
            celebration.remove();
        }, 3000);
    }

    createConfetti() {
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'fixed pointer-events-none z-50';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'][Math.floor(Math.random() * 5)];
            confetti.style.animation = `fall ${Math.random() * 3 + 2}s linear forwards`;
            
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                confetti.remove();
            }, 5000);
        }
        
        // Add CSS animation if not exists
        if (!document.getElementById('confetti-style')) {
            const style = document.createElement('style');
            style.id = 'confetti-style';
            style.textContent = `
                @keyframes fall {
                    to {
                        transform: translateY(100vh) rotate(360deg);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Network Statistics
    updateNetworkStatsDisplay() {
        // This could update a network statistics panel if implemented
        console.log('Network Stats:', this.networkStats);
    }

    updateAverageConfirmationTime(duration) {
        const totalTime = this.networkStats.averageConfirmationTime * (this.networkStats.successfulTransactions - 1) + duration;
        this.networkStats.averageConfirmationTime = totalTime / this.networkStats.successfulTransactions;
    }

    // Demo Functions
    runDemoScenario(scenario) {
        switch (scenario) {
            case 'quick_deposit':
                this.startDepositSimulation(0.05);
                break;
            case 'large_deposit':
                this.startDepositSimulation(1.5);
                break;
            case 'small_withdrawal':
                this.startWithdrawalSimulation('bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 0.01);
                break;
            case 'large_withdrawal':
                this.startWithdrawalSimulation('bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 2.0);
                break;
            case 'multiple_transactions':
                this.runMultipleTransactionDemo();
                break;
            default:
                app.showToast('Unknown demo scenario', 'error');
        }
    }

    async runMultipleTransactionDemo() {
        app.showToast('Running multiple transaction demo...', 'info');
        
        // Start multiple transactions with delays
        setTimeout(() => this.startDepositSimulation(0.1), 0);
        setTimeout(() => this.startDepositSimulation(0.25), 2000);
        setTimeout(() => this.startWithdrawalSimulation('bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 0.05), 4000);
        setTimeout(() => this.startDepositSimulation(0.5), 6000);
    }

    // Utility Functions
    getStatusDisplayText(status) {
        const displayTexts = {
            'initiated': 'Initiated',
            'broadcasting': 'Broadcasting',
            'pending': 'Confirming',
            'approved': 'Approved',
            'completed': 'Completed',
            'failed': 'Failed',
            'rejected': 'Rejected',
            'flagged': 'Flagged'
        };

        return displayTexts[status] || status.charAt(0).toUpperCase() + status.slice(1);
    }

    getStatusColor(status) {
        const colors = {
            'completed': 'text-green-400',
            'pending': 'text-yellow-400',
            'failed': 'text-red-400',
            'rejected': 'text-red-400',
            'flagged': 'text-purple-400',
            'initiated': 'text-blue-400',
            'broadcasting': 'text-indigo-400',
            'approved': 'text-green-400'
        };

        return colors[status] || 'text-gray-400';
    }

    // Settings Management
    updateSimulationSettings(newSettings) {
        this.simulationSettings = { ...this.simulationSettings, ...newSettings };
    }

    getSimulationSettings() {
        return { ...this.simulationSettings };
    }

    // Cleanup
    destroy() {
        this.activeSimulations.clear();
        
        // Remove progress container
        const container = document.getElementById('simulation-progress-container');
        if (container) {
            container.remove();
        }
    }
}

// Initialize simulation
const bitcoinSimulation = new BitcoinSimulation();

// Add demo scenarios to global scope for easy access
window.runDemo = (scenario) => {
    bitcoinSimulation.runDemoScenario(scenario);
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    bitcoinSimulation.destroy();
});

