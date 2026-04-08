/**
 * OrdexWallet - Main Application Logic
 */

// Global state
let currentPage = 'dashboard';
let walletExists = false;
let walletData = null;
let refreshInterval = null;

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
});

async function initApp() {
    try {
        const health = await ApiService.getHealth();
        
        if (!health.wallet_ready) {
            showPage('wallet-setup');
            return;
        }
        
        walletExists = true;
        await loadDashboardData();
        startAutoRefresh();
        
    } catch (e) {
        console.error('Failed to initialize:', e);
        showPage('wallet-setup');
    }
}

function startAutoRefresh() {
    refreshInterval = setInterval(async () => {
        if (currentPage === 'dashboard') {
            await loadDashboardData();
        }
    }, 30000);
}

// Navigation
function showPage(pageId) {
    currentPage = pageId;
    
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById(pageId).classList.remove('hidden');
    
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    const activeLink = document.querySelector(`nav a[href="#${pageId}"]`);
    if (activeLink) activeLink.classList.add('active');
    
    switch (pageId) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'wallet':
            loadWalletData();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'system':
            loadSystemData();
            break;
    }
}

// Dashboard
async function loadDashboardData() {
    try {
        const assets = await ApiService.getAssets();
        
        // Update OXC
        const oxcStatus = document.getElementById('oxc-status');
        if (assets.ordexcoin.sync_status.connected) {
            if (assets.ordexcoin.sync_status.syncing) {
                oxcStatus.className = 'status status-syncing';
                oxcStatus.innerHTML = '<span class="status-dot"></span> Syncing';
            } else {
                oxcStatus.className = 'status status-connected';
                oxcStatus.innerHTML = '<span class="status-dot"></span> Connected';
            }
        } else {
            oxcStatus.className = 'status status-disconnected';
            oxcStatus.innerHTML = '<span class="status-dot"></span> Disconnected';
        }
        
        document.getElementById('oxc-balance').innerHTML = 
            `${UI.formatAmount(assets.ordexcoin.balance)} <span class="balance-symbol">OXC</span>`;
        
        // Update OXG
        const oxgStatus = document.getElementById('oxg-status');
        if (assets.ordexgold.sync_status.connected) {
            if (assets.ordexgold.sync_status.syncing) {
                oxgStatus.className = 'status status-syncing';
                oxgStatus.innerHTML = '<span class="status-dot"></span> Syncing';
            } else {
                oxgStatus.className = 'status status-connected';
                oxgStatus.innerHTML = '<span class="status-dot"></span> Connected';
            }
        } else {
            oxgStatus.className = 'status status-disconnected';
            oxgStatus.innerHTML = '<span class="status-dot"></span> Disconnected';
        }
        
        document.getElementById('oxg-balance').innerHTML = 
            `${UI.formatAmount(assets.ordexgold.balance)} <span class="balance-symbol">OXG</span>`;
        
        // Update total
        const total = assets.ordexcoin.balance + assets.ordexgold.balance;
        document.getElementById('total-balance').innerHTML = 
            `${UI.formatAmount(total)} <span class="balance-symbol">OXC + OXG</span>`;
        
        // Load recent transactions
        loadRecentTransactions();
        
    } catch (e) {
        console.error('Failed to load dashboard:', e);
    }
}

async function loadRecentTransactions() {
    try {
        const result = await ApiService.getTransactions({ limit: 5 });
        const container = document.getElementById('recent-tx');
        
        if (result.transactions.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No transactions yet</div>';
            return;
        }
        
        container.innerHTML = result.transactions.map(tx => `
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-address">${UI.formatAddress(tx.address)}</div>
                    <div class="tx-time">${tx.category} &middot; ${UI.formatTime(tx.time)}</div>
                </div>
                <div class="tx-amount ${tx.amount >= 0 ? 'positive' : 'negative'}">
                    ${tx.amount >= 0 ? '+' : ''}${UI.formatAmount(tx.amount)}
                </div>
            </div>
        `).join('');
        
    } catch (e) {
        console.error('Failed to load recent transactions:', e);
    }
}

// Wallet Setup
function showCreateWallet() {
    showPage('wallet');
    showWalletTab('backup');
    document.getElementById('create-wallet-section').classList.remove('hidden');
}

async function createWallet() {
    const passphrase = document.getElementById('create-passphrase').value;
    
    try {
        NotificationService.info('Creating wallet...');
        const result = await ApiService.createWallet(passphrase);
        
        NotificationService.success('Wallet created successfully!');
        walletExists = true;
        
        showPage('wallet');
        
    } catch (e) {
        NotificationService.error(e.message);
    }
}

async function importWallet() {
    const privateKey = document.getElementById('import-key').value;
    const network = document.getElementById('import-network').value;
    const passphrase = document.getElementById('import-passphrase').value;
    
    if (!privateKey) {
        NotificationService.error('Please enter your private key');
        return;
    }
    
    try {
        NotificationService.info('Importing wallet...');
        const result = await ApiService.importWallet(privateKey, network, passphrase);
        
        NotificationService.success('Wallet imported successfully!');
        walletExists = true;
        
        showPage('wallet');
        
    } catch (e) {
        NotificationService.error(e.message);
    }
}

// Wallet Page
async function loadWalletData() {
    try {
        const info = await ApiService.getWalletInfo();
        
        if (!info.has_wallet) {
            // Show no wallet message
            document.getElementById('wallet-oxc-balance').innerHTML = 
                '<span class="text-muted">No wallet</span>';
            document.getElementById('wallet-oxg-balance').innerHTML = 
                '<span class="text-muted">No wallet</span>';
            document.getElementById('wallet-no-wallet').classList.remove('hidden');
            return;
        }
        
        document.getElementById('wallet-no-wallet')?.classList.add('hidden');
        
        document.getElementById('wallet-oxc-balance').innerHTML = 
            `${UI.formatAmount(info.ordexcoin.balance)} <span class="balance-symbol">OXC</span>`;
        document.getElementById('wallet-oxg-balance').innerHTML = 
            `${UI.formatAmount(info.ordexgold.balance)} <span class="balance-symbol">OXG</span>`;
        
        // Load receive addresses
        const oxcAddresses = await ApiService.getReceiveAddresses('ordexcoin');
        const oxgAddresses = await ApiService.getReceiveAddresses('ordexgold');
        
        if (oxcAddresses.addresses.length > 0) {
            document.querySelector('#oxc-address .address-text').textContent = 
                oxcAddresses.addresses[0].address;
        }
        
        if (oxgAddresses.addresses.length > 0) {
            document.querySelector('#oxg-address .address-text').textContent = 
                oxgAddresses.addresses[0].address;
        }
        
    } catch (e) {
        console.error('Failed to load wallet data:', e);
    }
}

function showWalletTab(tabName) {
    document.querySelectorAll('.wallet-tab').forEach(t => t.classList.add('hidden'));
    document.getElementById(`wallet-${tabName}`).classList.remove('hidden');
    
    document.querySelectorAll('#wallet .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
}

async function generateAddress(network) {
    try {
        const result = await ApiService.generateReceiveAddress(network);
        
        const addressEl = document.querySelector(`#${network === 'ordexcoin' ? 'oxc' : 'oxg'}-address .address-text`);
        addressEl.textContent = result.address;
        
        NotificationService.success('New address generated');
    } catch (e) {
        NotificationService.error(e.message);
    }
}

function copyAddress(btn) {
    const address = btn.previousElementSibling.textContent;
    UI.copyToClipboard(address);
}

async function sendTransaction() {
    const network = document.getElementById('send-network').value;
    const address = document.getElementById('send-address').value;
    const amount = document.getElementById('send-amount').value;
    const fee = document.getElementById('send-fee').value || null;
    
    if (!address || !amount) {
        NotificationService.error('Please fill in all required fields');
        return;
    }
    
    try {
        NotificationService.info('Sending transaction...');
        
        const result = await ApiService.sendTransaction(address, amount, network, fee);
        
        NotificationService.success(`Transaction sent! TXID: ${UI.formatAddress(result.txid, 16)}`);
        
        document.getElementById('send-address').value = '';
        document.getElementById('send-amount').value = '';
        
        showPage('transactions');
        
    } catch (e) {
        NotificationService.error(e.message);
    }
}

async function createBackup() {
    const passphrase = document.getElementById('backup-passphrase').value;
    
    try {
        const result = await ApiService.createBackup(passphrase);
        NotificationService.success('Backup created successfully!');
    } catch (e) {
        NotificationService.error(e.message);
    }
}

async function restoreBackup() {
    const fileInput = document.getElementById('restore-file');
    const passphrase = document.getElementById('restore-passphrase').value;
    
    if (!fileInput.files.length) {
        NotificationService.error('Please select a backup file');
        return;
    }
    
    NotificationService.info('Restoring wallet...');
    NotificationService.warning('Restore functionality requires backend implementation');
}

// Transactions
async function loadTransactions() {
    try {
        const network = document.getElementById('tx-filter-network').value;
        const category = document.getElementById('tx-filter-category').value;
        
        const result = await ApiService.getTransactions({ 
            network: network || undefined,
            category: category || undefined,
            limit: 50 
        });
        
        const container = document.getElementById('tx-list');
        
        if (result.transactions.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No transactions found</div>';
            return;
        }
        
        container.innerHTML = result.transactions.map(tx => `
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-address">${UI.formatAddress(tx.address)}</div>
                    <div class="tx-time">
                        ${tx.network} &middot; ${tx.category} &middot; ${UI.formatTime(tx.time)}
                    </div>
                </div>
                <div class="tx-amount ${tx.amount >= 0 ? 'positive' : 'negative'}">
                    ${tx.amount >= 0 ? '+' : ''}${UI.formatAmount(tx.amount)}
                </div>
            </div>
        `).join('');
        
    } catch (e) {
        console.error('Failed to load transactions:', e);
    }
}

// System
async function loadSystemData() {
    try {
        const stats = await ApiService.getSystemStats();
        
        // Disk
        document.getElementById('disk-total').textContent = stats.disk.total_gb;
        document.getElementById('disk-used').textContent = stats.disk.used_gb;
        document.getElementById('disk-percent').textContent = stats.disk.percent + '%';
        
        // Memory
        document.getElementById('mem-total').textContent = stats.memory.total_gb;
        document.getElementById('mem-used').textContent = stats.memory.used_gb;
        document.getElementById('mem-percent').textContent = stats.memory.percent + '%';
        
        // Network
        document.getElementById('net-sent').textContent = (stats.network.bytes_sent / 1024 / 1024).toFixed(1);
        document.getElementById('net-recv').textContent = (stats.network.bytes_recv / 1024 / 1024).toFixed(1);
        
        // Load daemon configs
        await loadDaemonConfigs();
        
        // Load logs
        await loadAuditLogs();
        
    } catch (e) {
        console.error('Failed to load system data:', e);
    }
}

async function loadDaemonConfigs() {
    try {
        const config = await ApiService.getDaemonConfig();
        
        const ordexcoindContainer = document.getElementById('ordexcoind-config');
        ordexcoindContainer.innerHTML = renderConfigForm('ordexcoind', config.ordexcoind);
        
        const ordexgolddContainer = document.getElementById('ordexgoldd-config');
        ordexgolddContainer.innerHTML = renderConfigForm('ordexgoldd', config.ordexgoldd);
        
    } catch (e) {
        console.error('Failed to load daemon config:', e);
    }
}

function renderConfigForm(daemon, config) {
    const fields = ['dbcache', 'maxconnections', 'maxmempool', 'minchainfreespace'];
    
    return fields.map(field => `
        <div class="form-group">
            <label class="form-label">${field}</label>
            <input type="number" id="${daemon}-${field}" class="form-input" value="${config[field] || ''}">
        </div>
    `).join('');
}

async function saveDaemonConfig(daemon) {
    const fields = ['dbcache', 'maxconnections', 'maxmempool', 'minchainfreespace'];
    const config = {};
    
    fields.forEach(field => {
        const value = document.getElementById(`${daemon}-${field}`).value;
        if (value) config[field] = parseInt(value);
    });
    
    try {
        await ApiService.updateDaemonConfig(daemon, config);
        NotificationService.success('Configuration saved');
    } catch (e) {
        NotificationService.error(e.message);
    }
}

function showSystemTab(tabName) {
    document.querySelectorAll('.system-tab').forEach(t => t.classList.add('hidden'));
    document.getElementById(`system-${tabName}`).classList.remove('hidden');
    
    document.querySelectorAll('#system .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
}

function handleConsoleKeypress(event) {
    if (event.key === 'Enter') {
        executeConsoleCommand();
    }
}

async function executeConsoleCommand() {
    const input = document.getElementById('console-input');
    const command = input.value.trim();
    
    if (!command) return;
    
    const daemon = document.getElementById('console-daemon').value;
    const output = document.getElementById('console-output');
    
    output.innerHTML += `<div class="mt-1"><span class="text-muted">$</span> ${command}</div>`;
    
    try {
        const result = await ApiService.executeRpc(command, [], daemon);
        output.innerHTML += `<div class="text-success">${JSON.stringify(result.result, null, 2)}</div>`;
    } catch (e) {
        output.innerHTML += `<div class="text-error">${e.message}</div>`;
    }
    
    output.scrollTop = output.scrollHeight;
    input.value = '';
}

async function loadAuditLogs() {
    try {
        const result = await ApiService.getLogs({ limit: 50 });
        
        const container = document.getElementById('audit-logs');
        
        if (result.logs.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No logs yet</div>';
            return;
        }
        
        container.innerHTML = result.logs.map(log => `
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-address">${log.category}</div>
                    <div class="tx-time">${log.level} &middot; ${log.created_at}</div>
                </div>
                <div class="text-muted">${UI.formatAddress(log.message, 20)}</div>
            </div>
        `).join('');
        
    } catch (e) {
        console.error('Failed to load logs:', e);
    }
}

// Make functions globally accessible
window.showPage = showPage;
window.createWallet = createWallet;
window.importWallet = importWallet;
window.showWalletTab = showWalletTab;
window.generateAddress = generateAddress;
window.copyAddress = copyAddress;
window.sendTransaction = sendTransaction;
window.createBackup = createBackup;
window.restoreBackup = restoreBackup;
window.showSystemTab = showSystemTab;
window.saveDaemonConfig = saveDaemonConfig;
window.handleConsoleKeypress = handleConsoleKeypress;
window.executeConsoleCommand = executeConsoleCommand;
window.copyToClipboard = UI.copyToClipboard;