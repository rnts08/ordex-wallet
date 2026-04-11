import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ordex_web_wallet.rpc import CLIContext, DaemonManager


class TestConcurrency:
    def test_cli_context_isolation(self):
        results = {}

        def user_operation(user_id: int, chain: str):
            ctx = CLIContext(
                cli_path="/usr/local/bin/ordexcoin-cli",
                chain=chain,
                wallet_name=f"wallet_{user_id}_{chain}",
                rpc_user="ordex",
                rpc_pass="password",
                rpc_port=5332,
                data_dir="/data",
            )
            wallet_name = ctx.wallet_name
            results[user_id] = wallet_name
            time.sleep(0.1)
            return wallet_name

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(1, 5):
                futures.append(executor.submit(user_operation, i, "ordexcoin"))

            for future in as_completed(futures):
                pass

        assert len(set(results.values())) == 4, (
            "Each user should have isolated wallet names"
        )

        for user_id, wallet_name in results.items():
            assert wallet_name == f"wallet_{user_id}_ordexcoin"

    def test_daemon_manager_concurrent_wallet_creation(self):
        manager = DaemonManager(
            cli_path="/usr/local/bin/ordexcoin-cli",
            rpc_user="ordex",
            rpc_pass="password",
            data_dir="/data",
        )

        created_wallets = []
        lock = threading.Lock()

        def create_wallet(user_id: int):
            wallet_name = f"wallet_{user_id}_ordexcoin"
            with lock:
                created_wallets.append(wallet_name)
            return wallet_name

        with patch.object(manager, "create_user_wallet") as mock_create:
            mock_create.side_effect = lambda uid, chain, pw: create_wallet(uid)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_wallet, i) for i in range(10)]
                for f in as_completed(futures):
                    pass

            assert len(created_wallets) == 10

    def test_concurrent_wallet_operations_no_cross_contamination(self):
        user_data = {}

        def simulate_user_session(user_id: int):
            user_data[user_id] = {
                "balance": 0.0,
                "addresses": [],
            }

            ctx = CLIContext(
                cli_path="/usr/local/bin/ordexcoin-cli",
                chain="ordexcoin",
                wallet_name=f"wallet_{user_id}_ordexcoin",
                rpc_user="ordex",
                rpc_pass="password",
            )

            user_data[user_id]["balance"] = 100.0 + user_id
            user_data[user_id]["addresses"].append(f"addr_{user_id}_1")
            time.sleep(0.05)
            user_data[user_id]["addresses"].append(f"addr_{user_id}_2")

            return user_data[user_id]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(simulate_user_session, i): i for i in range(1, 6)
            }

            for future in as_completed(futures):
                user_id = futures[future]
                result = future.result()
                assert result["balance"] == 100.0 + user_id
                assert len(result["addresses"]) == 2
                assert f"addr_{user_id}_1" in result["addresses"]
                assert f"addr_{user_id}_2" in result["addresses"]

    def test_wallet_loading_thread_safety(self):
        manager = DaemonManager(
            cli_path="/usr/local/bin/ordexcoin-cli",
            rpc_user="ordex",
            rpc_pass="password",
        )

        loaded_wallets = []
        errors = []

        def load_and_verify(user_id: int, chain: str):
            try:
                wallet_name = f"wallet_{user_id}_{chain}"
                manager.load_wallet(chain, wallet_name)
                loaded_wallets.append(wallet_name)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for user_id in range(1, 11):
            for chain in ["ordexcoin", "ordexgold"]:
                t = threading.Thread(target=load_and_verify, args=(user_id, chain))
                threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(loaded_wallets) == 20

    def test_is_wallet_loaded_concurrent_check(self):
        manager = DaemonManager(
            cli_path="/usr/local/bin/ordexcoin-cli",
            rpc_user="ordex",
            rpc_pass="password",
        )

        results = {}

        def check_wallet(user_id: int, chain: str):
            wallet_name = f"wallet_{user_id}_{chain}"
            is_loaded = manager.is_wallet_loaded(chain, wallet_name)
            results[f"{user_id}_{chain}"] = is_loaded

        threads = []
        for user_id in range(1, 6):
            for chain in ["ordexcoin", "ordexgold"]:
                t = threading.Thread(target=check_wallet, args=(user_id, chain))
                threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 10


class TestRPCClient:
    def test_rpc_client_basic_call(self):
        from ordex_web_wallet.rpc import RPCClient

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": {"balance": 100.0},
                "error": None,
                "id": 1,
            }
            mock_post.return_value = mock_response

            client = RPCClient("http://localhost:5332", "ordex", "password")
            result = client.call("getbalance")

            assert result == {"balance": 100.0}
            mock_post.assert_called_once()

    def test_rpc_client_error_handling(self):
        from ordex_web_wallet.rpc import RPCClient, RPCError

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": None,
                "error": {"code": -18, "message": "Wallet not found"},
                "id": 1,
            }
            mock_post.return_value = mock_response

            client = RPCClient("http://localhost:5332", "ordex", "password")

            with pytest.raises(RPCError) as exc_info:
                client.call("getbalance")

            assert exc_info.value.code == -18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
