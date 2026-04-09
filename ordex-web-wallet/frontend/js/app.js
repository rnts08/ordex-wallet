(function() {
    'use strict';

    const API_BASE = '/api';
    let authToken = localStorage.getItem('authToken');
    let isAdminUser = localStorage.getItem('isAdmin') === 'true';

    function showPage(pageId) {
        document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
        const page = document.getElementById('page-' + pageId);
        if (page) page.classList.remove('hidden');
        updateNav();
        
        if (pageId === 'dashboard') loadDashboard();
        if (pageId === 'admin') loadAdmin();
    }

    function updateNav() {
        const loggedIn = !!authToken;
        document.getElementById('nav-login').classList.toggle('hidden', loggedIn);
        document.getElementById('nav-register').classList.toggle('hidden', loggedIn);
        document.getElementById('nav-dashboard').classList.toggle('hidden', !loggedIn);
        document.getElementById('nav-send').classList.toggle('hidden', !loggedIn);
        document.getElementById('nav-receive').classList.toggle('hidden', !loggedIn);
        document.getElementById('nav-history').classList.toggle('hidden', !loggedIn);
        document.getElementById('nav-backup').classList.toggle('hidden', !loggedIn);
        document.getElementById('nav-admin').classList.toggle('hidden', !loggedIn || !isAdminUser);
        document.getElementById('nav-logout').classList.toggle('hidden', !loggedIn);
    }

    function showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.toggle('hidden', !show);
    }

    function showError(elementId, message) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = message;
            el.classList.remove('hidden');
        }
    }

    function hideError(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.classList.add('hidden');
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
        e.preventDefault();
        showLoading();
        hideError('login-error');
        
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        const res = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
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
        
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const passphrase = document.getElementById('register-passphrase').value;
        
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
        showPage('home');
    };

    async function loadDashboard() {
        const balanceRes = await apiRequest('/wallet/balance');
        document.getElementById('oxc-balance').textContent = (balanceRes.ordexcoin || 0).toFixed(8);
        document.getElementById('oxg-balance').textContent = (balanceRes.ordexgold || 0).toFixed(8);

        const addrRes = await apiRequest('/wallet/addresses');
        document.getElementById('oxc-address').textContent = addrRes.ordexcoin || 'No address';
        document.getElementById('oxg-address').textContent = addrRes.ordexgold || 'No address';
    }

    window.handleSend = async function(e) {
        e.preventDefault();
        showLoading();
        hideError('send-error');
        
        const chain = document.getElementById('send-chain').value;
        const address = document.getElementById('send-address').value;
        const amount = parseFloat(document.getElementById('send-amount').value);
        
        const res = await apiRequest('/wallet/send', {
            method: 'POST',
            body: JSON.stringify({ chain, address, amount }),
        });
        
        if (res.error) {
            showError('send-error', res.error);
        } else {
            alert('Sent! TX: ' + res.txid);
            document.getElementById('send-address').value = '';
            document.getElementById('send-amount').value = '';
            loadDashboard();
        }
        showLoading(false);
    };

    window.copyAddress = function(elementId) {
        const text = document.getElementById(elementId).textContent;
        navigator.clipboard.writeText(text);
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
        document.getElementById('stat-wallets').textContent = stats.total_wallets || 0;

        const users = await apiRequest('/admin/users');
        const tbody = document.getElementById('admin-users-table');
        tbody.innerHTML = users.map(u => 
            '<tr>' +
                '<td>' + u.id + '</td>' +
                '<td>' + u.username + '</td>' +
                '<td>' + u.email + '</td>' +
                '<td>' + new Date(u.created_at).toLocaleDateString() + '</td>' +
                '<td>' + (u.is_active ? 'Active' : 'Disabled') + '</td>' +
                '<td>' +
                    (u.is_active 
                        ? '<button class="btn btn-small" onclick="disableUser(' + u.id + ')">Disable</button>'
                        : '<button class="btn btn-small" onclick="enableUser(' + u.id + ')">Enable</button>'
                    ) +
                '</td>' +
            '</tr>'
        ).join('');
    }

    window.disableUser = async function(userId) {
        if (!confirm('Disable this user?')) return;
        await apiRequest('/admin/users/' + userId + '/disable', { method: 'POST' });
        loadAdmin();
    };

    window.enableUser = async function(userId) {
        await apiRequest('/admin/users/' + userId + '/enable', { method: 'POST' });
        loadAdmin();
    };

    window.showPage = showPage;

    function checkServices() {
        fetch(API_BASE + '/system/health')
            .then(r => r.json())
            .then(data => {
                const statusEl = document.getElementById('loading-status');
                const services = data.services || {};
                const dbHealthy = services.database?.status === 'healthy';
                
                if (dbHealthy) {
                    showLoading(false);
                    if (statusEl) statusEl.textContent = 'Ready';
                } else {
                    if (statusEl) statusEl.textContent = 'Connecting database...';
                    setTimeout(checkServices, 3000);
                }
            })
            .catch(() => {
                const statusEl = document.getElementById('loading-status');
                if (statusEl) statusEl.textContent = 'Connecting...';
                setTimeout(checkServices, 3000);
            });
    }

    if (authToken) {
        updateNav();
        showPage('dashboard');
        if (isAdminUser) loadAdmin();
    } else {
        showPage('home');
    }
    
    checkServices();
})();