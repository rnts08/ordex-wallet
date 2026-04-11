import pytest
import json
from unittest.mock import patch, MagicMock

class TestAdminWorkflowE2E:
    """End-to-end tests for the admin panel functionality."""

    def test_admin_stats_and_status(self, client, admin_token, mock_rpc):
        """Test retrieving system statistics."""
        with patch("ordex_web_wallet.middleware.auth.is_admin", return_value=True), \
             patch("ordex_web_wallet.api.admin.get_system_stats") as mock_stats:
            mock_stats.return_value = {"total_users": 5, "active_users": 5, "active_sessions": 3, "total_wallets": 10, "total_transactions": 20, "total_addresses": 5}
            mock_rpc.get_total_balance.return_value = 1000.5
            
            response = client.get(
                "/api/admin/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "total_users" in data
            assert data["total_oxc"] == 1000.5

    def test_admin_user_management(self, client, admin_token):
        """Test user listing, details, and status updates."""
        user_id = 99
        
        # Mock database for listing and details
        with patch("ordex_web_wallet.middleware.auth.is_admin", return_value=True), \
             patch("ordex_web_wallet.api.admin.get_users_paged") as mock_paged, \
             patch("ordex_web_wallet.database.get_user_by_id") as mock_get_id, \
             patch("ordex_web_wallet.database.get_user_wallets") as mock_wallets, \
             patch("ordex_web_wallet.database.DATABASE.execute_write") as mock_write:
            
            mock_paged.return_value = [{"id": user_id, "username": "target_user", "is_active": True}]
            mock_get_id.return_value = {"id": user_id, "username": "target_user", "email": "a@b.com", "is_admin": False, "is_active": True, "created_at": "2024-01-01", "last_login": None, "two_factor_enabled": False}
            mock_wallets.return_value = [{"chain": "ordexcoin", "wallet_name": "w1"}]
            
            # 1. List Users
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            assert len(json.loads(response.data)) == 1
            
            # 2. Get Details
            response = client.get(
                f"/api/admin/users/{user_id}/details",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["username"] == "target_user"
            assert len(data["wallets"]) == 1
            
            # 3. Disable User
            response = client.post(
                f"/api/admin/users/{user_id}/disable",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            mock_write.assert_called() # Should call update_user_status and admin_audit_log

    def test_admin_sensitive_actions(self, client, admin_token, mock_rpc):
        """Test password reset and wallet sweep."""
        user_id = 99
        
        with patch("ordex_web_wallet.middleware.auth.is_admin", return_value=True), \
             patch("ordex_web_wallet.api.admin.update_password") as mock_pw:
            
            # 1. Reset Password
            response = client.post(
                f"/api/admin/users/{user_id}/reset-password",
                json={"new_password": "NewPassword123!"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            mock_pw.assert_called_once()
            
            # 2. Sweep Wallet
            mock_rpc.get_user_balance.return_value = "50.0"
            mock_rpc.send_to_address.return_value = "sweep_txid_123"
            
            response = client.post(
                f"/api/admin/users/{user_id}/sweep",
                json={"admin_address": "AdminAddr123"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["ordexcoin"]["txid"] == "sweep_txid_123"

    def test_admin_audit_log_retrieval(self, client, admin_token):
        """Test viewing audit logs."""
        with patch("ordex_web_wallet.database.DATABASE.execute") as mock_exec:
            mock_exec.return_value = [
                {"id": 1, "admin_username": "admin", "action": "disable_user", "target_username": "user1", "created_at": "2024-01-01"}
            ]
            
            response = client.get(
                "/api/admin/audit",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]["action"] == "disable_user"
