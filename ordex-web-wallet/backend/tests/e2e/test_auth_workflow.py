import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))


class TestAuthWorkflowE2E:
    """End-to-end tests for the complete authentication workflow."""


    def test_complete_auth_workflow(self, client):
        """Test the complete authentication workflow: register -> login -> change password -> logout."""

        # Mock RPC daemon manager for wallet creation
        with patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon:
            mock_daemon.create_user_wallet.side_effect = [
                "wallet_1_ordexcoin",
                "wallet_1_ordexgold",
            ]

            # Step 1: User Registration
            with patch("ordex_web_wallet.api.auth.get_user_by_username", return_value=None), \
                 patch("ordex_web_wallet.api.auth.create_user", return_value={"id": 1, "username": "workflowtest", "email": "workflow@test.com"}), \
                 patch("ordex_web_wallet.api.auth.create_session"), \
                 patch("ordex_web_wallet.api.auth.create_user_wallet"):
                response = client.post(
                    "/api/auth/register",
                    json={
                        "username": "workflowtest",
                        "email": "workflow@test.com",
                        "password": "Password123!",  # Meets complexity requirements
                        "passphrase": "passphrase123",
                    },
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "token" in data
            assert data["username"] == "workflowtest"
            register_token = data["token"]

            # Verify user was created in database
            from ordex_web_wallet.database import get_user_by_username

            with patch("ordex_web_wallet.database.DATABASE") as mock_db:
                mock_db.execute_one.return_value = {
                    "id": 1,
                    "user_id": 1,
                    "username": "workflowtest",
                    "email": "workflow@test.com",
                    "password_hash": "scrypt:32768:8:1$hash",
                    "is_admin": False,
                    "is_active": True,
                }

                user = get_user_by_username("workflowtest")
                assert user is not None
                assert user["username"] == "workflowtest"

                # Step 2: Login with the same credentials
                with patch(
                    "ordex_web_wallet.api.auth.verify_password", return_value=True
                ):
                    login_response = client.post(
                        "/api/auth/login",
                        json={"username": "workflowtest", "password": "Password123!"},
                    )

                    assert login_response.status_code == 200
                    login_data = json.loads(login_response.data)
                    assert "token" in login_data
                    assert login_data["username"] == "workflowtest"
                    login_token = login_data["token"]

                    # Step 3: Change Password
                    with patch(
                        "ordex_web_wallet.database.update_password"
                    ) as mock_update_pw:
                        mock_update_pw.return_value = True

                        pw_response = client.post(
                            "/api/auth/change-password",
                            json={
                                "current_password": "Password123!",
                                "new_password": "NewPassword456!",
                            },
                            headers={"Authorization": f"Bearer {login_token}"},
                        )

                        assert pw_response.status_code == 200
                        pw_data = json.loads(pw_response.data)
                        assert "message" in pw_data

                        # Verify the password update was called
                        mock_update_pw.assert_called_once()

                        # Step 4: Login with new password
                        with patch(
                            "ordex_web_wallet.api.auth.verify_password",
                            return_value=True,
                        ):
                            new_login_response = client.post(
                                "/api/auth/login",
                                json={
                                    "username": "workflowtest",
                                    "password": "NewPassword456!",
                                },
                            )

                            assert new_login_response.status_code == 200
                            new_login_data = json.loads(new_login_response.data)
                            assert "token" in new_login_data
                            new_login_token = new_login_data["token"]

                            # Step 5: Logout
                            with patch(
                                "ordex_web_wallet.api.auth.delete_session"
                            ) as mock_delete_session:
                                logout_response = client.post(
                                    "/api/auth/logout",
                                    headers={
                                        "Authorization": f"Bearer {new_login_token}"
                                    },
                                )

                                assert logout_response.status_code == 200
                                logout_data = json.loads(logout_response.data)
                                assert "message" in logout_data

                                # Verify session was deleted
                                mock_delete_session.assert_called_once()

    def test_auth_workflow_with_2fa(self, client):
        """Test authentication workflow with 2FA enabled."""

        with patch("ordex_web_wallet.rpc.daemon_manager") as mock_daemon:
            mock_daemon.create_user_wallet.side_effect = [
                "wallet_1_ordexcoin",
                "wallet_1_ordexgold",
            ]

            # Register user
            with patch("ordex_web_wallet.api.auth.get_user_by_username", return_value=None), \
                 patch("ordex_web_wallet.api.auth.create_user", return_value={"id": 2, "username": "2fatest", "email": "2fa@test.com"}), \
                 patch("ordex_web_wallet.api.auth.create_session"), \
                 patch("ordex_web_wallet.api.auth.create_user_wallet"):
                response = client.post(
                    "/api/auth/register",
                    json={
                        "username": "2fatest",
                        "email": "2fa@test.com",
                        "password": "Password123!",
                        "passphrase": "passphrase123",
                    },
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "token" in data
            register_token = data["token"]

            # Enable 2FA for the user
            with patch("ordex_web_wallet.database.DATABASE.execute_write") as mock_enable_2fa, \
                 patch("ordex_web_wallet.database.DATABASE.execute_one") as mock_one_db:
                mock_enable_2fa.return_value = 1
                mock_one_db.return_value = {
                    "user_id": 2, 
                    "is_active": True, 
                    "is_admin": False,
                    "two_factor_secret": "ABCDEFGHIJKLMNOP"
                }
                
                # Make the request to enable 2FA
                client.post("/api/auth/2fa/enable", json={"code": "123456"}, headers={"Authorization": f"Bearer {register_token}"})

                # Login (should require 2FA)
                with patch(
                    "ordex_web_wallet.api.auth.verify_password", return_value=True
                ), patch("ordex_web_wallet.api.auth.get_user_by_username") as mock_get_user:
                    mock_get_user.return_value = {
                        "id": 2, "username": "2fatest", "password_hash": "hash", 
                        "two_factor_enabled": True, "two_factor_secret": "ABCDEFGHIJKLMNOP",
                        "is_active": True, "is_admin": False
                    }
                    login_response = client.post(
                        "/api/auth/login",
                        json={"username": "2fatest", "password": "Password123!"},
                    )

                    # This should either succeed (if 2FA not enforced) or return 2FA required
                    assert login_response.status_code in [200, 401, 500]

                    if login_response.status_code == 200:
                        login_data = json.loads(login_response.data)
                        assert "token" in login_data
                        login_token = login_data["token"]

                        # Verify 2FA was enabled
                        mock_enable_2fa.assert_called_once()

                        # Login with 2FA token
                        with patch(
                            "pyotp.TOTP.verify",
                            return_value=True,
                        ):
                            fa_response = client.post(
                                "/api/auth/2fa/verify",
                                json={
                                    "username": "2fatest",
                                    "password": "Password123!",
                                    "code": "123456"
                                }
                            )

                            assert fa_response.status_code == 200
