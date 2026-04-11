(function() {
    'use strict';

    const API_BASE = '/api';
    let authToken = localStorage.getItem('authToken');
    let isAdminUser = localStorage.getItem('isAdmin') === 'true';
    let currentBalances = { ordexcoin: 0, ordexgold: 0 };
    let adminPage = 1;
    let adminSearch = '';
    let txSearch = '';
    let searchTimeout = null;
    let txSearchTimeout = null;

    function safeGet(id) {
        const el = document.getElementById(id);
        if (!el) {
            console.warn(`Element with id "${id}" not found`);
        }
        return el;
    }

    function showPage(pageId) {
        document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
        const page = document.getElementById('page-' + pageId);
        if (page) page.classList.remove('hidden');
        updateNav();
        
        if (pageId === 'dashboard') loadDashboard();
        if (pageId === 'wallet') loadWallet();
        if (pageId === 'transactions') loadTransactions();
        if (pageId === 'settings') loadSettings();
        if (pageId === 'admin') loadAdmin();
        if (pageId === 'about') { /* Static page, no load needed */ }
        if (pageId === 'auth') {
            toggleAuthMode('login');
            refreshCaptcha();
        }
    }

    window.toggleAuthMode = function(mode) {
        const loginForm = safeGet('auth-login-form');
        const registerForm = safeGet('auth-register-form');
        const loginTab = safeGet('auth-tab-login');
        const registerTab = safeGet('auth-tab-register');
        
        if (mode === 'login') {
            if (loginForm) loginForm.classList.remove('hidden');
            if (registerForm) registerForm.classList.add('hidden');
            if (loginTab) loginTab.classList.add('active');
            if (registerTab) registerTab.classList.remove('active');
        } else {
            if (loginForm) loginForm.classList.add('hidden');
            if (registerForm) registerForm.classList.remove('hidden');
            if (loginTab) loginTab.classList.remove('active');
            if (registerTab) registerTab.classList.add('active');
            refreshCaptcha();
        }
    };

    let currentCaptcha = '';
    window.refreshCaptcha = function() {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
        currentCaptcha = '';
        for (let i = 0; i < 6; i++) {
            currentCaptcha += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        const el = safeGet('captcha-img');
        if (el) el.textContent = currentCaptcha;
    };

    function updateNav() {
        const loggedIn = !!authToken;
        const navItems = {
            'nav-login': loggedIn,
            'nav-register': loggedIn,
            'nav-dashboard': !loggedIn,
            'nav-wallet': !loggedIn,
            'nav-transactions': !loggedIn,
            'nav-settings': !loggedIn,
            'nav-about': false,
            'nav-admin': !loggedIn || !isAdminUser,
            'nav-logout': !loggedIn
        };

        for (const [id, hidden] of Object.entries(navItems)) {
            const el = document.getElementById(id);
            if (el) {
                el.classList.toggle('hidden', hidden);
            }
        }
    }

    function showLoading(show = true) {
        const overlay = safeGet('loading-overlay');
        if (overlay) overlay.classList.toggle('hidden', !show);
    }

    function showError(elementId, message) {
        const el = safeGet(elementId);
        if (el) {
            el.textContent = message;
            el.classList.remove('hidden');
        }
    }

    function hideError(elementId) {
        const el = safeGet(elementId);
        if (el) el.classList.add('hidden');
    }

    function showSuccess(elementId, message) {
        const el = safeGet(elementId);
        if (el) {
            el.textContent = message;
            el.classList.remove('hidden');
        }
    }

    function hideSuccess(elementId) {
        const el = safeGet(elementId);
        if (el) el.classList.add('hidden');
    }

    async function loadFeeConfig() {
        if (!isAdminUser) return;
        
        const chain = document.getElementById('fee-chain').value;
        try {
            const config = await apiRequest(`/admin/fees?chain=${chain}`);
            if (config && config.length > 0) {
                const fee = config[0];
                document.getElementById('fee-send').value = fee.send_fee_per_kb || '';
                document.getElementById('fee-receive').value = fee.receive_fee_percent || '';
                document.getElementById('fee-auto').checked = fee.use_auto_fee || false;
                document.getElementById('fee-admin-address').value = fee.admin_wallet_address || '';
            } else {
                // Set defaults if no config exists
                document.getElementById('fee-send').value = '0.001';
                document.getElementById('fee-receive').value = '0';
                document.getElementById('fee-auto').checked = true;
                document.getElementById('fee-admin-address').value = '';
            }
            hideError('fee-error');
        } catch (error) {
            showError('fee-error', 'Failed to load fee configuration');
        }
    }

    async function saveFeeConfig() {
        if (!isAdminUser) return;
        
        showLoading();
        try {
            const chain = document.getElementById('fee-chain').value;
            const sendFee = parseFloat(document.getElementById('fee-send').value) || 0.001;
            const receiveFee = parseFloat(document.getElementById('fee-receive').value) || 0;
            const useAuto = document.getElementById('fee-auto').checked;
            const adminAddress = document.getElementById('fee-admin-address').value.trim() || null;
            
            const response = await apiRequest('/admin/fees', {
                method: 'POST',
                body: JSON.stringify({
                    chain: chain,
                    send_fee_per_kb: sendFee,
                    receive_fee_percent: receiveFee,
                    use_auto_fee: useAuto,
                    admin_wallet_address: adminAddress
                })
            });
            
            showLoading(false);
            alert('Fee configuration saved successfully');
            loadFeeConfig(); // Reload to confirm save
        } catch (error) {
            showLoading(false);
            showError('fee-error', 'Failed to save fee configuration: ' + error.message);
        }
    }

    function apiRequest(endpoint, options = {}) {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken) headers['Authorization'] = 'Bearer ' + authToken;
        return fetch(API_BASE + endpoint, {
            ...options,
            headers: { ...headers, ...options.headers },
        }).then(r => r.json()).catch(err => ({ error: err.message }));
    }

    window.handleLogin = async function(e) {
        if (e) e.preventDefault();
        showLoading();
        hideError('login-error');
        
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const code = document.getElementById('login-2fa')?.value;
        
        const res = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password, code }),
        });
        
        if (res.error) {
            showError('login-error', res.error);
        } else {
            authToken = res.token;
            isAdminUser = res.is_admin;
            localStorage.setItem('authToken', res.token);
            localStorage.setItem('isAdmin', res.is_admin);
            updateNav();
            showPage('dashboard');
        }
        showLoading(false);
    };

    window.handleRegister = async function(e) {
        e.preventDefault();
        showLoading();
        hideError('register-error');
        
        const username = document.getElementById('register-username').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const passphrase = document.getElementById('register-passphrase').value;
        const captcha = document.getElementById('register-captcha').value.toUpperCase();
        
        if (captcha !== currentCaptcha) {
            showError('register-error', 'Invalid CAPTCHA code');
            showLoading(false);
            refreshCaptcha();
            return;
        }
        
        const confirmPassword = document.getElementById('register-confirm-password').value;
        if (password !== confirmPassword) {
            showError('register-error', 'Passwords do not match');
            showLoading(false);
            return;
        }
        
        if (password.length < 8 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
            showError('register-error', 'Password must be 8+ characters with uppercase, lowercase, and number');
            showLoading(false);
            return;
        }
        
        if (passphrase.length < 8) {
            showError('register-error', 'Passphrase must be at least 8 characters');
            showLoading(false);
            return;
        }
        
        const res = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password, passphrase }),
        });
        
        if (res.error) {
            showError('register-error', res.error);
        } else {
            authToken = res.token;
            isAdminUser = false;
            localStorage.setItem('authToken', res.token);
            localStorage.setItem('isAdmin', 'false');
            updateNav();
            showPage('dashboard');
        }
        showLoading(false);
    };

    window.logout = async function() {
        await apiRequest('/auth/logout', { method: 'POST' });
        authToken = null;
        isAdminUser = false;
        localStorage.removeItem('authToken');
        localStorage.removeItem('isAdmin');
        updateNav();
        showPage('login');
    };

    async function loadDashboard() {
        const balanceRes = await apiRequest('/wallet/balance');
        const oxcRaw = balanceRes.ordexcoin;
        const oxgRaw = balanceRes.ordexgold;
        
        const oxcBal = (typeof oxcRaw === 'number') ? oxcRaw : (parseFloat(oxcRaw) || 0);
        const oxgBal = (typeof oxgRaw === 'number') ? oxgRaw : (parseFloat(oxgRaw) || 0);
        
        currentBalances = { ordexcoin: oxcBal, ordexgold: oxgBal };
        
        document.getElementById('oxc-balance').innerHTML = oxcBal.toFixed(8) + ' <span class="balance-symbol">OXC</span>';
        document.getElementById('oxg-balance').innerHTML = oxgBal.toFixed(8) + ' <span class="balance-symbol">OXG</span>';
        
        const totalOxr = oxcBal + oxgBal;
        document.getElementById('total-balance').innerHTML = totalOxr.toFixed(8) + ' <span class="balance-symbol">OXC + OXG</span>';
        
        document.getElementById('oxc-status').className = 'status status-connected';
        document.getElementById('oxc-status').innerHTML = '<span class="status-dot"></span>Ready';
        document.getElementById('oxg-status').className = 'status status-connected';
        document.getElementById('oxg-status').innerHTML = '<span class="status-dot"></span>Ready';
        
        loadRecentTransactions();
    }

    async function loadWallet() {
        const balanceRes = await apiRequest('/wallet/balance');
        document.getElementById('wallet-oxc-balance').innerHTML = (parseFloat(balanceRes.ordexcoin) || 0).toFixed(8) + ' <span class="balance-symbol">OXC</span>';
        document.getElementById('wallet-oxg-balance').innerHTML = (parseFloat(balanceRes.ordexgold) || 0).toFixed(8) + ' <span class="balance-symbol">OXG</span>';
        currentBalances = { ordexcoin: parseFloat(balanceRes.ordexcoin) || 0, ordexgold: parseFloat(balanceRes.ordexgold) || 0 };
        
        const addrRes = await apiRequest('/wallet/addresses');
        const oxcAddr = (typeof addrRes.ordexcoin === 'string') ? addrRes.ordexcoin : '';
        const oxgAddr = (typeof addrRes.ordexgold === 'string') ? addrRes.ordexgold : '';

        document.getElementById('wallet-oxc-address').textContent = oxcAddr || 'No address';
        document.getElementById('wallet-oxg-address').textContent = oxgAddr || 'No address';
        
        const oxcEl = document.getElementById('oxc-address');
        const oxgEl = document.getElementById('oxg-address');
        
        if (oxcAddr && oxcAddr !== 'No address') {
            oxcEl.querySelector('.address-text').textContent = oxcAddr;
            oxcEl.classList.add('has-address');
        } else {
            oxcEl.querySelector('.address-text').textContent = 'No address - click Create Address';
            oxcEl.classList.remove('has-address');
        }
        
        if (oxgAddr && oxgAddr !== 'No address') {
            oxgEl.querySelector('.address-text').textContent = oxgAddr;
            oxgEl.classList.add('has-address');
        } else {
            oxgEl.querySelector('.address-text').textContent = 'No address - click Create Address';
            oxgEl.classList.remove('has-address');
        }
        
        document.getElementById('send-oxc-bal').textContent = (parseFloat(balanceRes.ordexcoin) || 0).toFixed(8);
        document.getElementById('send-oxg-bal').textContent = (parseFloat(balanceRes.ordexgold) || 0).toFixed(8);
        
        loadAddressBook();
    }

    async function loadAddressBook() {
        const addresses = await apiRequest('/wallet/address-book');
        const container = document.getElementById('address-book-list');
        
        if (!addresses || addresses.length === 0) {
            container.innerHTML = '<div class="text-muted text-center" style="padding: 20px;">No saved addresses</div>';
            return;
        }
        
        container.innerHTML = addresses.map(a => 
            '<div class="address-item">' +
                '<div>' +
                    '<div class="address-item-label">' + (a.label || 'Unlabeled') + '</div>' +
                    '<div class="address-item-address">' + a.address + '</div>' +
                '</div>' +
                '<div class="address-item-actions">' +
                    '<button class="btn btn-small" onclick="copyAddressText(\'' + a.address + '\')">Copy</button>' +
                    '<button class="btn btn-small" onclick="showAddressQR(\'' + a.address + '\', \'' + (a.label || 'Address').replace(/'/g, "\\'") + '\')">QR</button>' +
                    '<button class="btn btn-small" onclick="sendToAddress(\'' + a.address + '\')">Send</button>' +
                    '<button class="btn btn-small" onclick="archiveAddress(' + a.id + ')">Archive</button>' +
                '</div>' +
            '</div>'
        ).join('');
    }

    window.copyAddressText = function(text) {
        navigator.clipboard.writeText(text);
    };

    window.sendToAddress = function(address) {
        document.getElementById('send-address').value = address;
        showPage('wallet');
        showWalletTab('send');
    };

    window.archiveAddress = async function(addressId) {
        if (!confirm('Archive this address?')) return;
        await apiRequest('/wallet/addresses/' + addressId + '/archive', { method: 'POST' });
        loadAddressBook();
    };

    async function loadTransactions() {
        const txs = await apiRequest('/wallet/transactions');
        const container = document.getElementById('tx-list');
        
        if (!txs || txs.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding: 20px;">No transactions yet</div>';
            return;
        }
        
        const networkFilter = document.getElementById('tx-filter-network').value;
        const typeFilter = document.getElementById('tx-filter-category').value;
        const searchFilter = (document.getElementById('tx-search').value || '').toLowerCase();
        
        let filtered = txs;
        if (networkFilter) filtered = filtered.filter(t => t.chain === networkFilter);
        if (typeFilter) filtered = filtered.filter(t => t.type === typeFilter);
        if (searchFilter) {
            filtered = filtered.filter(t => 
                (t.address && t.address.toLowerCase().includes(searchFilter)) || 
                (t.txid && t.txid.toLowerCase().includes(searchFilter)) ||
                (t.label && t.label.toLowerCase().includes(searchFilter))
            );
        }
        
        container.innerHTML = filtered.map(tx => 
            '<div class="tx-item">' +
                '<div class="tx-info">' +
                    '<div class="tx-address">' + (tx.type === 'receive' ? 'Received' : 'Sent') + ' ' + tx.chain.toUpperCase() + '</div>' +
                    '<div class="tx-time">' + new Date(tx.timestamp).toLocaleString() + '</div>' +
                '</div>' +
                '<div class="tx-amount ' + (tx.type === 'receive' ? 'positive' : 'negative') + '">' +
                    (tx.type === 'receive' ? '+' : '-') + tx.amount.toFixed(8) + ' ' + tx.chain.toUpperCase().slice(0, 3) +
                '</div>' +
            '</div>'
        ).join('');
    }

    window.debounceTxSearch = function() {
        clearTimeout(txSearchTimeout);
        txSearchTimeout = setTimeout(() => {
            loadTransactions();
        }, 300);
    };

    async function loadRecentTransactions() {
        const txs = await apiRequest('/wallet/transactions');
        const container = document.getElementById('recent-tx');
        
        if (!txs || txs.length === 0) {
            container.innerHTML = '<div class="text-center text-muted" style="padding: 20px;">No transactions yet</div>';
            return;
        }
        
        container.innerHTML = txs.slice(0, 5).map(tx => 
            '<div class="tx-item">' +
                '<div class="tx-info">' +
                    '<div class="tx-address">' + (tx.type === 'receive' ? 'Received' : 'Sent') + ' ' + tx.chain.toUpperCase() + '</div>' +
                    '<div class="tx-time">' + new Date(tx.timestamp).toLocaleString() + '</div>' +
                '</div>' +
                '<div class="tx-amount ' + (tx.type === 'receive' ? 'positive' : 'negative') + '">' +
                    (tx.type === 'receive' ? '+' : '-') + tx.amount.toFixed(8) + ' ' + tx.chain.toUpperCase().slice(0, 3) +
                '</div>' +
            '</div>'
        ).join('');
    }

    window.handleSend = async function() {};

    window.calculateFee = function() {
        const chain = document.getElementById('send-network').value;
        const amount = parseFloat(document.getElementById('send-amount').value) || 0;
        const feeType = document.getElementById('send-fee-type').value;
        
        let fee = 0.001;
        if (feeType === 'manual') {
            fee = parseFloat(document.getElementById('send-fee').value) || 0.001;
        }
        
        document.getElementById('send-fee-display').textContent = fee.toFixed(8);
        document.getElementById('send-total-display').textContent = amount.toFixed(8);
        
        if (feeType === 'manual') {
            document.getElementById('send-fee').classList.remove('hidden');
        } else {
            document.getElementById('send-fee').classList.add('hidden');
        }
    };

    window.updateSendBalance = function() {
        const chain = document.getElementById('send-network').value;
        document.getElementById('send-oxc-bal').textContent = currentBalances.ordexcoin.toFixed(8);
        document.getElementById('send-oxg-bal').textContent = currentBalances.ordexgold.toFixed(8);
    };

    window.useMax = function() {
        const chain = document.getElementById('send-network').value;
        const balance = chain === 'ordexcoin' ? currentBalances.ordexcoin : currentBalances.ordexgold;
        const fee = parseFloat(document.getElementById('send-fee-type').value === 'manual' 
            ? (parseFloat(document.getElementById('send-fee').value) || 0.001) 
            : 0.001);
        const max = Math.max(0, balance - fee);
        document.getElementById('send-amount').value = max.toFixed(8);
        calculateFee();
    };

    window.openSendConfirm = function() {
        if (!validateSendForm()) {
            showError('send-error', 'Please fix the errors above');
            return;
        }
        
        const address = document.getElementById('send-address').value;
        const amount = parseFloat(document.getElementById('send-amount').value);
        
        const chain = document.getElementById('send-network').value;
        const fee = document.getElementById('send-fee-display').textContent;
        
        document.getElementById('confirm-send-network').textContent = chain === 'ordexcoin' ? 'OrdexCoin (OXC)' : 'OrdexGold (OXG)';
        document.getElementById('confirm-send-address').textContent = address;
        document.getElementById('confirm-send-amount').textContent = amount.toFixed(8) + ' ' + chain.toUpperCase().slice(0, 3);
        document.getElementById('confirm-send-fee').textContent = fee;
        document.getElementById('confirm-send-total').textContent = (amount + parseFloat(fee)).toFixed(8) + ' ' + chain.toUpperCase().slice(0, 3);
        
        document.getElementById('modal-send-confirm').classList.remove('hidden');
    };

    window.closeSendConfirmModal = function() {
        document.getElementById('modal-send-confirm').classList.add('hidden');
    };

    window.executeSend = async function() {
        hideError('send-confirm-error');
        showLoading();
        
        const chain = document.getElementById('send-network').value;
        const address = document.getElementById('send-address').value;
        const amount = parseFloat(document.getElementById('send-amount').value);
        const fee = document.getElementById('send-fee-type').value === 'manual' 
            ? parseFloat(document.getElementById('send-fee').value) 
            : null;
        
        const res = await apiRequest('/wallet/send', {
            method: 'POST',
            body: JSON.stringify({ chain, address, amount, fee }),
        });
        
        if (res.error) {
            showError('send-confirm-error', res.error);
            showLoading(false);
            return;
        }
        
        closeSendConfirmModal();
        document.getElementById('send-address').value = '';
        document.getElementById('send-amount').value = '';
        loadDashboard();
        alert('Sent! TX: ' + res.txid);
        showLoading(false);
    };

    window.copyAddress = function(btn) {
        const text = btn.previousElementSibling.textContent;
        navigator.clipboard.writeText(text);
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
    };

    window.showQR = function(chain) {
        const oxc = document.getElementById('oxc-address').querySelector('.address-text').textContent;
        const oxg = document.getElementById('oxg-address').querySelector('.address-text').textContent;
        const address = chain === 'ordexcoin' ? oxc : oxg;
        const title = chain === 'ordexcoin' ? 'OrdexCoin (OXC)' : 'OrdexGold (OXG)';
        showAddressQR(address, title);
    };

    window.showAddressQR = function(address, title = 'Address') {
        if (!address || address.includes('No address')) return;
        
        const modal = document.getElementById('modal-qr');
        document.getElementById('qr-address').textContent = address;
        
        const qrContainer = document.getElementById('qr-code');
        qrContainer.innerHTML = ''; // Clear previous content
        
        // Local QR generation
        new QRCode(qrContainer, {
            text: address,
            width: 200,
            height: 200,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
        
        modal.classList.remove('hidden');
    };

    window.closeQRModal = function() {
        document.getElementById('modal-qr').classList.add('hidden');
    };

    window.generateNewAddress = async function(chain) {
        let label = prompt('Enter label (optional):');
        if (label && label.length > 64) label = label.substring(0, 64);
        showLoading();
        
        const res = await apiRequest('/wallet/addresses/generate', {
            method: 'POST',
            body: JSON.stringify({ chain, label }),
        });
        
        if (res.error) {
            alert(res.error);
        } else {
            loadWallet();
        }
        showLoading(false);
    };

    window.showWalletTab = function(tabId) {
        document.querySelectorAll('.wallet-tab').forEach(t => t.classList.add('hidden'));
        document.getElementById('wallet-' + tabId).classList.remove('hidden');
        
        document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
        event.target.classList.add('active');
        
        if (tabId === 'send') {
            updateSendBalance();
        }
        if (tabId === 'import-export') {
            loadExportAddress();
        }
        if (tabId === 'addresses') {
            loadAddressBook();
        }
    };
    
    window.importWif = async function() {
        hideError('import-error');
        
        const network = document.getElementById('import-network').value;
        const wif = document.getElementById('import-wif').value;
        const passphrase = document.getElementById('import-passphrase').value;
        
        if (!wif) {
            showError('import-error', 'Private key required');
            return;
        }
        
        showLoading();
        
        const res = await apiRequest('/wallet/import-wif', {
            method: 'POST',
            body: JSON.stringify({ chain: network, wif, passphrase }),
        });
        
        if (res.error) {
            showError('import-error', res.error);
        } else {
            document.getElementById('import-wif').value = '';
            document.getElementById('import-passphrase').value = '';
            loadWallet();
            alert('Key imported successfully!');
        }
        showLoading(false);
    };
    
    window.loadExportAddress = async function() {
        const network = document.getElementById('export-network').value;
        const addrRes = await apiRequest('/wallet/addresses');
        document.getElementById('export-address').textContent = addrRes[network] || 'No address';
        document.getElementById('export-wif').textContent = '********';
    };
    
    window.revealExportWif = function() {
        const confirmed = document.getElementById('export-confirm').checked;
        if (!confirmed) {
            showError('export-error', 'Please confirm you understand the risk');
            return;
        }
        
        hideError('export-error');
        
        const network = document.getElementById('export-network').value;
        apiRequest('/wallet/export-wif', {
            method: 'POST',
            body: JSON.stringify({ chain: network }),
        }).then(res => {
            if (res.error) {
                showError('export-error', res.error);
            } else {
                document.getElementById('export-wif').textContent = res.wif || 'Error';
            }
        });
    };
    
    window.exportWif = async function() {
        const confirmed = document.getElementById('export-confirm').checked;
        if (!confirmed) {
            showError('export-error', 'Please confirm you understand the risk');
            return;
        }
        
        hideError('export-error');
        
        const network = document.getElementById('export-network').value;
        
        showLoading();
        
        const res = await apiRequest('/wallet/export-wif', {
            method: 'POST',
            body: JSON.stringify({ chain: network }),
        });
        
        if (res.error) {
            showError('export-error', res.error);
        } else {
            const key = res.wif;
            navigator.clipboard.writeText(key);
            document.getElementById('export-wif').textContent = key;
            alert('Private key copied to clipboard!');
        }
        showLoading(false);
    };

    window.openQuickSendModal = function() {
        document.getElementById('modal-quick-send').classList.remove('hidden');
        updateQuickSendBalance();
    };

    window.closeQuickSendModal = function() {
        document.getElementById('modal-quick-send').classList.add('hidden');
        document.getElementById('quick-send-address').value = '';
        document.getElementById('quick-send-amount').value = '';
    };

    window.updateQuickSendBalance = function() {
        const chain = document.getElementById('quick-send-network').value;
        const balance = chain === 'ordexcoin' ? currentBalances.ordexcoin : currentBalances.ordexgold;
        document.getElementById('quick-send-balance').textContent = balance.toFixed(8) + ' ' + chain.toUpperCase().slice(0, 3);
    };

    window.calculateQuickSendFee = function() {
        const amount = parseFloat(document.getElementById('quick-send-amount').value) || 0;
        const feeType = document.getElementById('quick-send-fee-type').value;
        
        let fee = 0.001;
        if (feeType === 'manual') {
            fee = parseFloat(document.getElementById('quick-send-fee').value) || 0.001;
            document.getElementById('quick-send-fee').classList.remove('hidden');
        } else {
            document.getElementById('quick-send-fee').classList.add('hidden');
        }
        
        document.getElementById('quick-send-fee-display').textContent = fee.toFixed(8);
        document.getElementById('quick-send-total-display').textContent = amount.toFixed(8);
    };

    window.useMaxQuickSend = function() {
        const chain = document.getElementById('quick-send-network').value;
        const balance = chain === 'ordexcoin' ? currentBalances.ordexcoin : currentBalances.ordexgold;
        const fee = document.getElementById('quick-send-fee-type').value === 'manual' 
            ? (parseFloat(document.getElementById('quick-send-fee').value) || 0.001) 
            : 0.001;
        const max = Math.max(0, balance - fee);
        document.getElementById('quick-send-amount').value = max.toFixed(8);
        calculateQuickSendFee();
    };

    window.confirmQuickSend = function() {
        if (!validateQuickSendForm()) {
            showError('quick-send-error', 'Please fix the errors above');
            return;
        }
        
        const address = document.getElementById('quick-send-address').value;
        const amount = parseFloat(document.getElementById('quick-send-amount').value);
        
        const chain = document.getElementById('quick-send-network').value;
        const fee = document.getElementById('quick-send-fee-type').value === 'manual' 
            ? parseFloat(document.getElementById('quick-send-fee').value) 
            : null;
        
        apiRequest('/wallet/send', {
            method: 'POST',
            body: JSON.stringify({ chain, address, amount, fee }),
        }).then(res => {
            if (res.error) {
                showError('quick-send-error', res.error);
            } else {
                closeQuickSendModal();
                loadDashboard();
                alert('Sent! TX: ' + res.txid);
            }
        });
    };

    async function loadSettings() {
        const settings = await apiRequest('/auth/settings');
        if (settings) {
            document.getElementById('setting-reminders').checked = settings.opt_out_reminders || false;
            document.getElementById('setting-notifications').checked = settings.opt_out_notifications || false;
            
            // Local storage preferences (Theme/Currency)
            const theme = localStorage.getItem('theme') || 'dark';
            const currency = localStorage.getItem('currency') || 'USD';
            document.getElementById('setting-theme').value = theme;
            document.getElementById('setting-currency').value = currency;
            setTheme(theme);
        }
    }

    window.saveSettings = async function() {
        const opt_out_reminders = document.getElementById('setting-reminders').checked;
        const opt_out_notifications = document.getElementById('setting-notifications').checked;
        const theme = document.getElementById('setting-theme').value;
        const currency = document.getElementById('setting-currency').value;
        
        showLoading();
        const res = await apiRequest('/auth/settings', {
            method: 'POST',
            body: JSON.stringify({ opt_out_reminders, opt_out_notifications })
        });
        
        if (!res.error) {
            localStorage.setItem('theme', theme);
            localStorage.setItem('currency', currency);
            setTheme(theme);
            alert('Settings saved successfully');
        } else {
            alert('Error saving settings: ' + res.error);
        }
        showLoading(false);
    };

    window.changeTheme = function() {
        const theme = document.getElementById('setting-theme').value;
        setTheme(theme);
    };

    function setTheme(theme) {
        document.body.classList.remove('theme-light', 'theme-dark');
        if (theme === 'light') {
            document.body.classList.add('theme-light');
        } else if (theme === 'dark') {
            document.body.classList.add('theme-dark');
        } else if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.body.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
        }
    }

    window.openDeleteAccountModal = function() {
        document.getElementById('modal-delete-account').classList.remove('hidden');
        document.getElementById('delete-confirm-password').value = '';
        hideError('delete-account-error');
    };

    window.closeDeleteAccountModal = function() {
        document.getElementById('modal-delete-account').classList.add('hidden');
    };

    window.executeDeleteAccount = async function() {
        const password = document.getElementById('delete-confirm-password').value;
        if (!password) {
            showError('delete-account-error', 'Password required');
            return;
        }
        
        if (!confirm('FINAL WARNING: This will permanently delete your account. Are you absolutely sure?')) return;
        
        showLoading();
        const res = await apiRequest('/auth/delete', {
            method: 'POST',
            body: JSON.stringify({ password })
        });
        
        if (res.error) {
            showError('delete-account-error', res.error);
            showLoading(false);
        } else {
            alert('Your account has been deleted. We are sorry to see you go.');
            logout();
            showLoading(false);
        }
    };

    window.handleChangePassword = async function() {
        hideError('password-error');
        hideSuccess('password-success');
        
        const current = document.getElementById('current-password').value;
        const newPwd = document.getElementById('new-password').value;
        const confirm = document.getElementById('confirm-new-password').value;
        
        if (!current || !newPwd || !confirm) {
            showError('password-error', 'All fields required');
            return;
        }
        
        if (newPwd !== confirm) {
            showError('password-error', 'New passwords do not match');
            return;
        }
        
        if (newPwd.length < 8 || !/[A-Z]/.test(newPwd) || !/[a-z]/.test(newPwd) || !/\d/.test(newPwd)) {
            showError('password-error', 'Password must be 8+ chars with uppercase, lowercase, number');
            return;
        }
        
        const res = await apiRequest('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({ current_password: current, new_password: newPwd }),
        });
        
        if (res.error) {
            showError('password-error', res.error);
        } else {
            showSuccess('password-success', 'Password changed successfully');
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-new-password').value = '';
        }
    };

    window.showSetup2FA = async function() {
        document.getElementById('2fa-status').classList.add('hidden');
        document.getElementById('2fa-setup').classList.remove('hidden');
        
        const res = await apiRequest('/auth/2fa/setup', { method: 'POST' });
        if (res.qrcode) {
            document.getElementById('2fa-qrcode').innerHTML = '<img src="' + res.qrcode + '" alt="2FA QR Code">';
        }
    };

    window.verifyAndEnable2FA = async function() {
        const code = document.getElementById('2fa-code').value;
        const res = await apiRequest('/auth/2fa/enable', {
            method: 'POST',
            body: JSON.stringify({ code }),
        });
        
        if (res.error) {
            alert(res.error);
        } else {
            alert('2FA enabled!');
            cancel2FA();
        }
    };

    window.cancel2FA = function() {
        document.getElementById('2fa-status').classList.remove('hidden');
        document.getElementById('2fa-setup').classList.add('hidden');
        document.getElementById('2fa-code').value = '';
    };

    async function createBackup() {
        showLoading();
        const res = await apiRequest('/backup/create', { method: 'POST' });
        if (res.backup) {
            const a = document.createElement('a');
            a.href = 'data:application/octet-stream;base64,' + res.backup;
            a.download = 'ordex-web-wallet-backup-' + Date.now() + '.dat';
            a.click();
        }
        showLoading(false);
    }

    async function loadAdmin() {
        if (!isAdminUser) return;
        
        const stats = await apiRequest('/admin/stats');
        document.getElementById('stat-users').textContent = stats.total_users || 0;
        document.getElementById('stat-active').textContent = stats.active_users || 0;
        document.getElementById('stat-sessions').textContent = stats.active_sessions || 0;
        document.getElementById('stat-wallets').textContent = stats.total_wallets || 0;
        document.getElementById('stat-oxc').textContent = (parseFloat(stats.total_oxc) || 0).toFixed(8);
        document.getElementById('stat-oxg').textContent = (parseFloat(stats.total_oxg) || 0).toFixed(8);
        document.getElementById('stat-tx').textContent = stats.total_transactions || 0;
        
        const dbSize = parseInt(stats.database_size) || 0;
        document.getElementById('stat-db-size').textContent = formatBytes(dbSize);
        
        const sortSelect = document.getElementById('user-sort');
        const [sortBy, sortOrder] = (sortSelect?.value || 'created_at:DESC').split(':');
        
        const offset = (adminPage - 1) * 25;
        const users = await apiRequest(`/admin/users?limit=25&offset=${offset}&sort_by=${sortBy}&sort_order=${sortOrder}&search=${encodeURIComponent(adminSearch)}`);
        
        const tbody = document.getElementById('admin-users-table');
        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No users found</td></tr>';
        } else {
            tbody.innerHTML = users.map(u => 
                '<tr>' +
                    '<td>' + u.id + '</td>' +
                    '<td>' + u.username + '</td>' +
                    '<td>' + (u.email || '-') + '</td>' +
                    '<td>' + (u.wallet_count || 0) + '</td>' +
                    '<td>' + new Date(u.created_at).toLocaleDateString() + '</td>' +
                    '<td>' + (u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never') + '</td>' +
                    '<td><span class="' + (u.is_active ? 'status status-connected' : 'status status-disconnected') + '">' + (u.is_active ? 'Active' : 'Disabled') + '</span></td>' +
                    '<td>' + (u.two_factor_enabled ? 'Yes' : 'No') + '</td>' +
                     '<td>' +
                         '<button class="btn btn-small" onclick="viewUserDetails(' + u.id + ')">Details</button>' +
                         ' ' +
                         (u.is_active 
                             ? '<button class="btn btn-small" onclick="disableUser(' + u.id + ', \'' + u.username + '\')">Disable</button>'
                             : '<button class="btn btn-small" onclick="enableUser(' + u.id + ', \'' + u.username + '\')">Enable</button>'
                         ) +
                         '<button class="btn btn-small" onclick="resetUserPassword(' + u.id + ', \'' + u.username + '\')">Reset</button>' +
                         '<button class="btn btn-small" onclick="sweepUserWallet(' + u.id + ', \'' + u.username + '\')">Sweep</button>' +
                         '<button class="btn btn-small btn-danger" onclick="deleteUser(' + u.id + ', \'' + u.username + '\')">Delete</button>' +
                     '</td>' +
                '</tr>'
            ).join('');
        }
        
        const countRes = await apiRequest(`/admin/users/count?search=${encodeURIComponent(adminSearch)}`);
        const totalUsers = countRes?.count || 0;
        const totalPages = Math.ceil(totalUsers / 25);
        document.getElementById('page-info').textContent = `Page ${adminPage} of ${totalPages}`;
        document.getElementById('prev-page').disabled = adminPage <= 1;
        document.getElementById('next-page').disabled = adminPage >= totalPages;
        
        loadAuditLog();
    }
    
    window.formatBytes = function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    window.debounceSearch = function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            adminSearch = document.getElementById('user-search').value;
            adminPage = 1;
            loadAdmin();
        }, 300);
    };
    
    window.changePage = function(delta) {
        adminPage += delta;
        loadAdmin();
    };

    window.loadAuditLog = async function() {
        const logs = await apiRequest('/admin/audit');
        const container = document.getElementById('audit-log');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="text-muted text-center" style="padding: 20px;">No audit logs</div>';
            return;
        }
        
        container.innerHTML = logs.map(l => 
            '<div class="audit-item">' +
                '<div class="audit-time">' + new Date(l.created_at).toLocaleString() + '</div>' +
                '<div class="audit-action">' +
                    '<strong>' + l.admin_username + '</strong> ' + l.action +
                    (l.target_username ? ' <span class="audit-target">@' + l.target_username + '</span>' : '') +
                '</div>' +
            '</div>'
        ).join('');
    };

window.disableUser = async function(userId, username) {
        if (!confirm('Disable user "' + username + '"?\n\nThey will not be able to log in until re-enabled.')) return;
        if (!confirm('Are you absolutely sure? This will prevent all access.')) return;
        await apiRequest('/admin/users/' + userId + '/disable', { method: 'POST' });
        loadAdmin();
    };

    window.enableUser = async function(userId, username) {
        if (!confirm('Enable user "' + username + '"?')) return;
        await apiRequest('/admin/users/' + userId + '/enable', { method: 'POST' });
        loadAdmin();
    };

    window.resetUserPassword = async function(userId, username) {
        const newPwd = prompt('Enter new password for user "' + username + '":');
        if (!newPwd) return;
        
        if (newPwd.length < 8 || !/[A-Z]/.test(newPwd) || !/[a-z]/.test(newPwd) || !/\d/.test(newPwd)) {
            alert('Password must be at least 8 characters with uppercase, lowercase, and number');
            return;
        }
        
        if (!confirm('Reset password for "' + username + '"?\n\nNew password: ' + newPwd)) return;
        
        await apiRequest('/admin/users/' + userId + '/reset-password', {
            method: 'POST',
            body: JSON.stringify({ new_password: newPwd }),
        });
        alert('Password reset for ' + username);
    };

    window.sweepUserWallet = async function(userId, username) {
        const address = prompt('Enter admin destination address to sweep "' + username + '"\'s wallet to:');
        if (!address) return;
        
        if (!confirm('WARNING: Sweep ALL funds from "' + username + '" to:\n' + address + '?\n\nThis cannot be undone!')) return;
        if (!confirm('Final confirmation: Transfer all coins to ' + address + '?')) return;
        
        showLoading();
        const res = await apiRequest('/admin/users/' + userId + '/sweep', {
            method: 'POST',
            body: JSON.stringify({ admin_address: address }),
        });
        
        let msg = 'Sweep complete for ' + username + ':\n\n';
        for (const chain of ['ordexcoin', 'ordexgold']) {
            if (res[chain]?.txid) {
                msg += chain.toUpperCase() + ': ' + res[chain].amount + ' sent\nTX: ' + res[chain].txid + '\n\n';
            } else if (res[chain]?.error) {
                msg += chain.toUpperCase() + ': Error - ' + res[chain].error + '\n\n';
            }
        }
        alert(msg);
        showLoading(false);
    };

window.deleteUser = async function(userId, username) {
        if (!confirm('DELETE this user and all their data? This cannot be undone.')) return;
        if (!confirm('Are you sure? All wallets and transactions will be permanently deleted.')) return;
        
        await apiRequest('/admin/users/' + userId, { method: 'DELETE' });
        loadAdmin();
    };

    window.viewUserDetails = async function(userId) {
        try {
            const user = await apiRequest(`/admin/users/${userId}/details`);
            
            // Create modal HTML
            const modalHtml = `
                <div class="modal-overlay" id="user-details-modal">
                    <div class="modal-content" style="max-width: 700px;">
                        <div class="modal-header">
                            <h3>User Details: ${user.username}</h3>
                            <button class="btn btn-small btn-close" onclick="document.getElementById('user-details-modal').remove()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="info-grid">
                                <div><strong>ID:</strong> ${user.id}</div>
                                <div><strong>Username:</strong> ${user.username}</div>
                                <div><strong>Email:</strong> ${user.email || 'Not set'}</div>
                                <div><strong>Admin:</strong> ${user.is_admin ? 'Yes' : 'No'}</div>
                                <div><strong>Active:</strong> ${user.is_active ? 'Yes' : 'No'}</div>
                                <div><strong>Created:</strong> ${new Date(user.created_at).toLocaleString()}</div>
                                <div><strong>Last Login:</strong> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</div>
                                <div><strong>2FA Enabled:</strong> ${user.two_factor_enabled ? 'Yes' : 'No'}</div>
                            </div>
                            
                            <div class="section-title">Actions</div>
                            <div class="modal-action-bar">
                                <button class="btn btn-secondary btn-small" onclick="document.getElementById('user-details-modal').remove(); sweepUserWallet(${user.id}, '${user.username}')">Sweep Wallet</button>
                                <button class="btn btn-secondary btn-small" onclick="document.getElementById('user-details-modal').remove(); promptDirectMessage(${user.id}, '${user.username}')">Send Message</button>
                                <button class="btn btn-secondary btn-small" onclick="document.getElementById('user-details-modal').remove(); resetUserPassword(${user.id}, '${user.username}')">Reset Password</button>
                            </div>

                            <div class="section-title">Recent Activity</div>
                            <div class="activity-list">
                                ${user.recent_activities && user.recent_activities.length > 0 
                                    ? user.recent_activities.map(activity => `
                                        <div class="activity-item">
                                            <span class="activity-time">${new Date(activity.timestamp).toLocaleString()}</span>
                                            <span class="activity-description">${activity.description}</span>
                                        </div>
                                    `).join('')
                                    : '<p>No recent activity</p>'
                                }
                            </div>
                            
                            <div class="section-title">Wallets</div>
                            <div class="wallet-list">
                                ${user.wallets && user.wallets.length > 0 
                                    ? user.wallets.map(wallet => `
                                        <div class="wallet-item">
                                            <span class="wallet-chain">${wallet.chain.toUpperCase()}</span>
                                            <span class="wallet-name">${wallet.wallet_name}</span>
                                            <span class="wallet-balance">${parseFloat(wallet.balance || 0).toFixed(8)} ${wallet.chain.toUpperCase().slice(0, 3)}</span>
                                        </div>
                                    `).join('')
                                    : '<p>No wallets found</p>'
                                }
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-danger" onclick="document.getElementById('user-details-modal').remove(); deleteUser(${user.id}, '${user.username}')">Delete User</button>
                            <button class="btn btn-secondary" onclick="document.getElementById('user-details-modal').remove()">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
        } catch (error) {
            alert('Failed to load user details: ' + error.message);
        }
    };

    window.promptDirectMessage = function(userId, username) {
        document.getElementById('nav-admin').click();
        showAdminTab('notifications');
        document.getElementById('direct-msg-target').value = userId;
        document.getElementById('direct-msg-title').value = 'System Message';
        document.getElementById('direct-msg-message').focus();
    };

    window.sendBroadcast = async function() {
        const title = document.getElementById('broadcast-title').value;
        const message = document.getElementById('broadcast-message').value;
        const type = document.getElementById('broadcast-type').value;
        
        if (!title || !message) {
            showError('broadcast-error', 'Title and message required');
            return;
        }
        
        showLoading();
        const res = await apiRequest('/admin/messages/broadcast', {
            method: 'POST',
            body: JSON.stringify({ title, message, type })
        });
        
        if (res.error) {
            showError('broadcast-error', res.error);
        } else {
            alert('Broadcast sent to all users');
            document.getElementById('broadcast-title').value = '';
            document.getElementById('broadcast-message').value = '';
        }
        showLoading(false);
    };

    window.sendDirectMessage = async function() {
        const userId = document.getElementById('direct-msg-target').value;
        const title = document.getElementById('direct-msg-title').value;
        const message = document.getElementById('direct-msg-message').value;
        
        if (!userId || !title || !message) {
            showError('direct-msg-error', 'User ID, title and message required');
            return;
        }
        
        showLoading();
        const res = await apiRequest('/admin/messages', {
            method: 'POST',
            body: JSON.stringify({ user_id: parseInt(userId), title, message })
        });
        
        if (res.error) {
            showError('direct-msg-error', res.error);
        } else {
            alert('Message sent to user ' + userId);
            document.getElementById('direct-msg-target').value = '';
            document.getElementById('direct-msg-title').value = '';
            document.getElementById('direct-msg-message').value = '';
        }
        showLoading(false);
    };

    window.clearExpiredSessions = async function() {
        if (!confirm('Clear all expired sessions?')) return;
        showLoading();
        const res = await apiRequest('/admin/maintenance/clear-sessions', { method: 'POST' });
        alert(res.message || 'Sessions cleared');
        showLoading(false);
    };

    window.rotateAuditLogs = async function() {
        if (!confirm('Rotate audit logs?')) return;
        showLoading();
        const res = await apiRequest('/admin/maintenance/rotate-logs', { method: 'POST' });
        alert(res.message || 'Logs rotated');
        showLoading(false);
    };

    window.backupDatabase = async function() {
        showLoading();
        const res = await apiRequest('/admin/maintenance/backup-db', { method: 'POST' });
        if (res.download_url) {
            window.open(res.download_url);
        } else {
            alert(res.message || 'Backup created on server');
        }
        showLoading(false);
    };

    window.toggleMaintenanceMode = async function() {
        const res = await apiRequest('/admin/maintenance/toggle', { method: 'POST' });
        alert('Maintenance mode: ' + (res.enabled ? 'ENABLED' : 'DISABLED'));
    };


    window.showAdminTab = function(tabId) {
        document.querySelectorAll('.admin-tab').forEach(t => t.classList.add('hidden'));
        document.getElementById('admin-' + tabId).classList.remove('hidden');
        
        document.querySelectorAll('#page-admin .tabs .tab').forEach(t => t.classList.remove('active'));
        event.target.classList.add('active');
        
        if (tabId === 'status') loadAdmin();
        if (tabId === 'users') loadAdmin();
        if (tabId === 'notifications') { /* Already initialized by UI */ }
        if (tabId === 'maintenance') {
            loadMaintenanceStatus();
        }
        if (tabId === 'audit') loadAuditLog();
        if (tabId === 'fees') loadFeeConfig();
    };

    async function loadMaintenanceStatus() {
        const health = await apiRequest('/system/health');
        document.getElementById('admin-oxc-sync').textContent = health.chains?.ordexcoin?.status || 'Unknown';
        document.getElementById('admin-oxg-sync').textContent = health.chains?.ordexgold?.status || 'Unknown';
    };

    window.showPage = showPage;

    function checkServices() {
        fetch(API_BASE + '/system/health')
            .then(r => r.json())
            .then(data => {
                const statusEl = document.getElementById('loading-status');
                if (statusEl) statusEl.textContent = 'Ready';
                showLoading(false);
            })
            .catch(() => {
                const statusEl = document.getElementById('loading-status');
                if (statusEl) statusEl.textContent = 'Connecting...';
                setTimeout(checkServices, 3000);
            });
    }

    // Validation Helpers
    window.validateAddress = function(address, chain) {
        if (!address) return false;
        const bech32Chars = "[023456789acdefghjklmnpqrstuvwxyz]";
        let pattern;
        if (chain === 'ordexcoin') {
            pattern = new RegExp(`^oxc1${bech32Chars}{38,59}$`, 'i');
        } else {
            pattern = new RegExp(`^oxg1${bech32Chars}{38,59}$`, 'i');
        }
        return pattern.test(address);
    };

    window.validateAmount = function(amount) {
        const val = parseFloat(amount);
        if (isNaN(val) || val <= 0) return false;
        const parts = amount.toString().split('.');
        if (parts.length > 1 && parts[1].length > 8) return false;
        return true;
    };

    window.validateSendForm = function() {
        const chain = document.getElementById('send-network').value;
        const address = document.getElementById('send-address').value.trim();
        const amount = document.getElementById('send-amount').value;
        
        const addrErr = document.getElementById('send-address-error');
        const amtErr = document.getElementById('send-amount-error');
        
        let isValid = true;
        
        if (address && !validateAddress(address, chain)) {
            addrErr.textContent = `Invalid ${chain === 'ordexcoin' ? 'OXC' : 'OXG'} address format`;
            addrErr.classList.remove('hidden');
            isValid = false;
        } else {
            addrErr.classList.add('hidden');
        }
        
        if (amount && !validateAmount(amount)) {
            amtErr.textContent = 'Invalid amount (must be positive, max 8 decimals)';
            amtErr.classList.remove('hidden');
            isValid = false;
        } else {
            amtErr.classList.add('hidden');
        }
        
        return isValid;
    };

    window.validateQuickSendForm = function() {
        const chain = document.getElementById('quick-send-network').value;
        const address = document.getElementById('quick-send-address').value.trim();
        const amount = document.getElementById('quick-send-amount').value;
        
        const addrErr = document.getElementById('quick-send-address-error');
        const amtErr = document.getElementById('quick-send-amount-error');
        
        let isValid = true;
        
        if (address && !validateAddress(address, chain)) {
            addrErr.textContent = `Invalid ${chain === 'ordexcoin' ? 'OXC' : 'OXG'} address format`;
            addrErr.classList.remove('hidden');
            isValid = false;
        } else {
            addrErr.classList.add('hidden');
        }
        
        if (amount && !validateAmount(amount)) {
            amtErr.textContent = 'Invalid amount (must be positive, max 8 decimals)';
            amtErr.classList.remove('hidden');
            isValid = false;
        } else {
            amtErr.classList.add('hidden');
        }
        
        return isValid;
    };

    if (authToken) {
        updateNav();
        showPage('dashboard');
    } else {
        showPage('auth');
    }
    
    checkServices();
})();