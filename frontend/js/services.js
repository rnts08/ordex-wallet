/**
 * OrdexWallet - API Service
 * Handles all communication with the Flask backend
 */

const API_BASE = window.location.origin + '/api';

class ApiService {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    static async post(endpoint, body) {
        return this.request(endpoint, { method: 'POST', body });
    }

    // Wallet
    static async createWallet(passphrase = '') {
        return this.post('/wallet/create', { passphrase });
    }

    static async importWallet(privateKey, network = 'ordexcoin', passphrase = '') {
        return this.post('/wallet/import', { private_key: privateKey, network, passphrase });
    }

    static async getWalletInfo() {
        return this.get('/wallet/info');
    }

    static async signMessage(address, message, network = 'ordexcoin') {
        return this.post('/wallet/sign-message', { address, message, network });
    }

    static async verifyMessage(address, signature, message, network = 'ordexcoin') {
        return this.post('/wallet/verify-message', { address, signature, message, network });
    }

    static async createBackup(passphrase = '') {
        return this.post('/wallet/backup', { passphrase });
    }

    // Assets
    static async getAssets() {
        return this.get('/assets');
    }

    static async getAsset(asset) {
        return this.get(`/assets/${asset}`);
    }

    // Transactions
    static async getTransactions(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.get(`/transactions${query ? '?' + query : ''}`);
    }

    static async getTransaction(txid) {
        return this.get(`/transactions/${txid}`);
    }

    static async sendTransaction(address, amount, network = 'ordexcoin', fee = null) {
        return this.post('/transactions/send', { address, amount, network, fee });
    }

    static async getReceiveAddresses(network = 'ordexcoin') {
        return this.get(`/transactions/receive?network=${network}`);
    }

    static async generateReceiveAddress(network = 'ordexcoin', label = '') {
        return this.post('/transactions/receive/generate', { network, label });
    }

    static async getSendAddresses(network = 'ordexcoin') {
        return this.get(`/transactions/send-addresses?network=${network}`);
    }

    // Market
    static async getPrices() {
        return this.get('/market/prices');
    }

    static async getNews() {
        return this.get('/market/news');
    }

    // System
    static async getHealth() {
        return this.get('/system/health');
    }

    static async getSystemStats() {
        return this.get('/system/stats');
    }

    static async getLogs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.get(`/system/logs${query ? '?' + query : ''}`);
    }

    static async getDaemonConfig() {
        return this.get('/system/config');
    }

    static async updateDaemonConfig(daemon, config) {
        return this.post('/system/config', { daemon, config });
    }

    static async executeRpc(command, params = [], daemon = 'ordexcoind') {
        return this.post('/system/rpc-console', { command, params, daemon });
    }
}

/**
 * OrdexWallet - Wallet Service
 * Manages wallet state and operations
 */
class WalletService {
    constructor() {
        this.wallet = null;
        this.assets = null;
    }

    async checkWalletExists() {
        try {
            const info = await ApiService.getWalletInfo();
            this.wallet = info;
            return true;
        } catch (e) {
            return false;
        }
    }

    async createWallet(passphrase = '') {
        const result = await ApiService.createWallet(passphrase);
        this.wallet = result.wallet;
        return result;
    }

    async importWallet(privateKey, network = 'ordexcoin', passphrase = '') {
        const result = await ApiService.importWallet(privateKey, network, passphrase);
        this.wallet = result.wallet;
        return result;
    }

    async refreshWalletInfo() {
        try {
            this.wallet = await ApiService.getWalletInfo();
            return this.wallet;
        } catch (e) {
            console.error('Failed to refresh wallet info:', e);
            return null;
        }
    }

    async refreshAssets() {
        try {
            this.assets = await ApiService.getAssets();
            return this.assets;
        } catch (e) {
            console.error('Failed to refresh assets:', e);
            return null;
        }
    }
}

/**
 * OrdexWallet - Notification Service
 * Handles user notifications
 */
class NotificationService {
    static show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container') || this.createContainer();
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        if (duration > 0) {
            setTimeout(() => {
                notification.remove();
            }, duration);
        }
    }

    static createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1000; max-width: 400px;';
        document.body.appendChild(container);
        return container;
    }

    static success(message) { this.show(message, 'success'); }
    static error(message) { this.show(message, 'error'); }
    static warning(message) { this.show(message, 'warning'); }
    static info(message) { this.show(message, 'info'); }
}

/**
 * OrdexWallet - UI Helpers
 */
const UI = {
    showPage(pageId) {
        document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
        document.getElementById(pageId).classList.remove('hidden');
        
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        const activeLink = document.querySelector(`nav a[href="#${pageId}"]`);
        if (activeLink) activeLink.classList.add('active');
    },

    showLoading(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    },

    formatAddress(address, chars = 8) {
        if (!address || address.length < chars * 2) return address;
        return address.substring(0, chars) + '...' + address.substring(address.length - chars);
    },

    formatAmount(amount, decimals = 8) {
        if (amount === null || amount === undefined) return '0';
        return parseFloat(amount).toFixed(decimals);
    },

    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    },

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            NotificationService.success('Copied to clipboard');
        } catch (e) {
            NotificationService.error('Failed to copy');
        }
    }
};

// Export for use in other modules
window.ApiService = ApiService;
window.WalletService = WalletService;
window.NotificationService = NotificationService;
window.UI = UI;