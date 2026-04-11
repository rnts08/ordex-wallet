import pytest
import json
from unittest.mock import patch, MagicMock

class TestMaintenanceWorkflowE2E:
    """End-to-end tests for maintenance features: address book, backup, encryption, WIF."""

    def test_address_book_workflow(self, client, user_token):
        """Test adding and archiving addresses in the address book."""
        # Mock database for address book
        with patch("ordex_web_wallet.api.wallet.DATABASE.execute") as mock_execute, \
             patch("ordex_web_wallet.api.wallet.DATABASE.execute_write") as mock_write:
            
            # Mock return for listing addresses
            mock_execute.return_value = [
                {"id": 1, "label": "Test Label", "address": "addr123", "chain": "ordexcoin", "archived": False}
            ]
            
            # Step 1: Get Address Book
            response = client.get(
                "/api/wallet/address-book",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) > 0
            assert data[0]["label"] == "Test Label"

            # Step 2: Archive Address
            response = client.post(
                "/api/wallet/addresses/1/archive",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 200
            assert json.loads(response.data)["message"] == "Address archived"
            mock_write.assert_called()

    def test_wallet_backup(self, client, user_token, mock_rpc):
        """Test wallet backup creation."""
        mock_rpc.backup_wallet.return_value = "/data/backups/wallet_1_ordexcoin_backup.dat"
        
        response = client.post(
            "/api/wallet/backup",
            json={"chain": "ordexcoin"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "path" in data
        assert "backup.dat" in data["path"]

    def test_wallet_encryption_workflow(self, client, user_token, mock_rpc):
        """Test wallet encryption and passphrase management."""
        
        # Step 1: Encrypt Wallet
        response = client.post(
            "/api/wallet/encrypt",
            json={"chain": "ordexcoin", "passphrase": "new_secure_pass"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert "encrypted successfully" in json.loads(response.data)["message"]
        
        # Step 2: Change Passphrase
        response = client.post(
            "/api/wallet/change-passphrase",
            json={
                "chain": "ordexcoin", 
                "old_passphrase": "new_secure_pass",
                "new_passphrase": "even_more_secure"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert "changed successfully" in json.loads(response.data)["message"]

    def test_wif_import_export(self, client, user_token, mock_rpc):
        """Test WIF key import and export."""
        mock_rpc.import_wif.return_value = "txid123"
        mock_rpc.export_wif.return_value = "5Kb8kLf9zgWQandp2fpY83T" # Example WIF
        
        # Step 1: Import WIF
        response = client.post(
            "/api/wallet/import-wif",
            json={"chain": "ordexcoin", "wif": "5Kb..."},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert json.loads(response.data)["imported"] is True

        # Step 2: Export WIF
        response = client.post(
            "/api/wallet/export-wif",
            json={"chain": "ordexcoin"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert "wif" in json.loads(response.data)
