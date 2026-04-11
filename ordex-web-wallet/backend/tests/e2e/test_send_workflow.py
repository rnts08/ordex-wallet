import pytest
import json
from unittest.mock import patch, MagicMock

class TestSendWorkflowE2E:
    """End-to-end tests for the send workflow with address book integration."""

    def test_send_transaction_success(self, client, user_token, mock_rpc):
        """Test successful send transaction."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.send_from_user.return_value = "txid123abc"

            response = client.post(
                "/api/wallet/send",
                json={
                    "chain": "ordexcoin",
                    "address": "DestinationAddress123",
                    "amount": 1.5,
                },
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "txid" in data
            assert data["txid"] == "txid123abc"

    def test_send_transaction_insufficient_funds(self, client, user_token, mock_rpc):
        """Test send transaction with insufficient funds."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.send_from_user.side_effect = Exception("Insufficient funds")

            response = client.post(
                "/api/wallet/send",
                json={
                    "chain": "ordexcoin",
                    "address": "DestinationAddress123",
                    "amount": 1000.0,
                },
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
            assert "Insufficient funds" in data["error"]

    def test_send_transaction_invalid_input(self, client, user_token):
        """Test send transaction with invalid input."""
        # Missing address
        response = client.post(
            "/api/wallet/send",
            json={
                "chain": "ordexcoin",
                "amount": 1.0,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 400
        assert "Valid address and amount required" in json.loads(response.data)["error"]

    def test_send_with_address_book_save(self, client, user_token, mock_rpc):
        """Test sending transaction and saving to address book."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets, \
             patch("ordex_web_wallet.api.wallet.DATABASE.execute_write") as mock_write:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.send_from_user.return_value = "txid789"
            mock_write.return_value = 1

            response = client.post(
                "/api/wallet/send",
                json={
                    "chain": "ordexcoin",
                    "address": "SaveMeToAddressBook",
                    "amount": 0.5,
                    "save_to_address_book": True,
                    "address_label": "My Friend's Address",
                },
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 200
            mock_write.assert_called()

    def test_quick_send_modal(self, client, user_token, mock_rpc):
        """Test quick send functionality."""
        with patch("ordex_web_wallet.api.wallet.get_user_wallets") as mock_wallets:
            mock_wallets.return_value = [
                {"chain": "ordexcoin", "wallet_name": "wallet_1_ordexcoin"},
            ]
            mock_rpc.send_from_user.return_value = "quicktx456"

            response = client.post(
                "/api/wallet/send",
                json={
                    "chain": "ordexcoin",
                    "address": "QuickSendAddress",
                    "amount": 0.01,
                },
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert response.status_code == 200
            assert json.loads(response.data)["txid"] == "quicktx456"
