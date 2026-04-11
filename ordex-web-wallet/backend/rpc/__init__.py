import os
import json
import requests
import time
import logging
from typing import Any, Optional
from datetime import datetime

from ordex_web_wallet.utils.logging_utils import log_rpc, rpc_logger


class RPCError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RPC Error {code}: {message}")


def sanitize_rpc_error(e: Exception) -> str:
    """Sanitize RPC errors to avoid leaking internal info."""
    err_str = str(e)

    if "Connection refused" in err_str or "could not connect" in err_str.lower():
        return "Cannot connect to the blockchain daemon. Please try again later."
    if "Insufficient funds" in err_str:
        return "Insufficient funds for this transaction."
    if "Invalid address" in err_str:
        return "The provided address is invalid."
    if "wallet not found" in err_str.lower():
        return "User wallet not found in the daemon."
    if "Invalid RPC handle" in err_str:
        return "Wallet not loaded in the daemon."

    return err_str


class HTTPRPCContext:
    """HTTP-based RPC context for direct daemon communication."""

    def __init__(
        self,
        chain: str,
        wallet_name: str = None,
        rpc_user: str = None,
        rpc_pass: str = None,
        rpc_port: int = None,
        rpc_host: str = None,
    ):
        self.chain = chain
        self.wallet_name = wallet_name
        self.rpc_user = rpc_user or os.getenv("RPC_USER", "ordex")
        self.rpc_pass = rpc_pass or os.getenv("RPC_PASS", "")
        self.rpc_port = rpc_port or (5332 if chain == "ordexcoin" else 5333)
        self.rpc_host = rpc_host or os.getenv(
            "RPC_HOST", "ordexcoind" if chain == "ordexcoin" else "ordexgoldd"
        )
        self.url = (
            f"http://{self.rpc_host}:{self.rpc_port}/wallet/{wallet_name}"
            if wallet_name
            else f"http://{self.rpc_host}:{self.rpc_port}"
        )

    def call(self, method: str, *args) -> Any:
        start_time = time.time()
        try:
            payload = {"method": method, "params": list(args), "id": 1}
            response = requests.post(
                self.url,
                json=payload,
                auth=(self.rpc_user, self.rpc_pass),
                timeout=30,
            )
            duration_ms = (time.time() - start_time) * 1000
            result = response.json()
            if result.get("error"):
                error = result["error"]
                log_rpc(
                    method,
                    self.chain,
                    success=False,
                    duration_ms=duration_ms,
                    error=error.get("message"),
                )
                raise RPCError(error.get("code", -1), error.get("message", "Unknown"))
            log_rpc(method, self.chain, success=True, duration_ms=duration_ms)
            return result.get("result")
        except requests.ConnectionError:
            duration_ms = (time.time() - start_time) * 1000
            log_rpc(
                method,
                self.chain,
                success=False,
                duration_ms=duration_ms,
                error="connection_refused",
            )
            raise RPCError(-1, f"Cannot connect to {self.chain} daemon at {self.url}")
        except requests.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            log_rpc(
                method,
                self.chain,
                success=False,
                duration_ms=duration_ms,
                error="timeout",
            )
            raise RPCError(-1, "RPC call timed out")


class DaemonManager:
    def __init__(
        self,
        rpc_user: str,
        rpc_pass: str,
        oxc_host: str = None,
        oxg_host: str = None,
        oxc_port: int = 5332,
        oxg_port: int = 5333,
    ):
        self.rpc_user = rpc_user
        self.rpc_pass = rpc_pass
        self.oxc_host = oxc_host or os.getenv("OXRPC_HOST", "ordexcoind")
        self.oxg_host = oxg_host or os.getenv("OGRPC_HOST", "ordexgoldd")
        self.oxc_port = int(os.getenv("OXRPC_PORT", oxc_port))
        self.oxg_port = int(os.getenv("OGRPC_PORT", oxg_port))
        self._session = requests.Session()
        self._session.auth = (rpc_user, rpc_pass)

    def _get_url(self, chain: str, wallet_name: str = None) -> str:
        host = self.oxc_host if chain == "ordexcoin" else self.oxg_host
        port = self.oxc_port if chain == "ordexcoin" else self.oxg_port
        if wallet_name:
            return f"http://{host}:{port}/wallet/{wallet_name}"
        return f"http://{host}:{port}"

    def _call(self, chain: str, method: str, *args, wallet_name: str = None):
        url = self._get_url(chain, wallet_name)
        payload = {"method": method, "params": list(args), "id": 1}
        try:
            response = self._session.post(url, json=payload, timeout=30)
            result = response.json()
            if result.get("error"):
                error = result["error"]
                raise RPCError(error.get("code", -1), error.get("message", "Unknown"))
            return result.get("result")
        except requests.ConnectionError:
            raise RPCError(-1, f"Cannot connect to {chain} daemon")
        except requests.Timeout:
            raise RPCError(-1, "RPC call timed out")

    def load_wallet(self, chain: str, wallet_name: str):
        url = self._get_url(chain)
        try:
            self._call(chain, "loadwallet", wallet_name)
        except RPCError as e:
            if "already loaded" in str(e).lower() or "already exists" in str(e).lower():
                pass
            else:
                raise e

    def is_wallet_loaded(self, chain: str, wallet_name: str) -> bool:
        try:
            wallets = self._call(chain, "listwallets")
            return wallet_name in (wallets or [])
        except:
            return False

    def _get_wallet_name(
        self, user_id: int = None, chain: str = None, user_guid: str = None
    ) -> str:
        """Generate wallet name from user_id or user_guid."""
        import uuid

        if user_guid:
            return f"wallet_{user_guid}_{chain}"
        elif user_id:
            return f"wallet_{user_id}_{chain}"
        else:
            return f"wallet_{uuid.uuid4().hex}_{chain}"

    def unlock_wallet(
        self,
        user_id: int = None,
        chain: str = None,
        passphrase: str = None,
        timeout: int = 3600,
        user_guid: str = None,
    ):
        wallet_name = self._get_wallet_name(user_id, chain, user_guid)
        try:
            return self._call(
                chain, "walletpassphrase", passphrase, timeout, wallet_name=wallet_name
            )
        except RPCError as e:
            if "already unlocked" in str(e).lower():
                return True
            raise e

    def create_user_wallet(
        self, user_id: int, chain: str, passphrase: str = None, user_guid: str = None
    ) -> str:
        if user_guid:
            wallet_name = f"wallet_{user_guid}_{chain}"
        else:
            import uuid

            wallet_name = f"wallet_{uuid.uuid4().hex}_{chain}"

        try:
            result = self._call(
                chain, "createwallet", wallet_name, False, False, passphrase or ""
            )
        except RPCError as e:
            if "already exists" in str(e).lower():
                pass
            else:
                raise e

        return wallet_name

    def delete_user_wallet(
        self, user_id: int, chain: str, user_guid: str = None
    ) -> bool:
        if user_guid:
            wallet_name = f"wallet_{user_guid}_{chain}"
        else:
            wallet_name = f"wallet_{user_id}_{chain}"
        try:
            unload_result = self._call(chain, "unloadwallet", wallet_name)
            return True
        except RPCError:
            return False

    def get_or_create_user_address(
        self, user_id: int, chain: str, user_guid: str = None
    ) -> str:
        if user_guid:
            wallet_name = f"wallet_{user_guid}_{chain}"
        else:
            wallet_name = f"wallet_{user_id}_{chain}"

        try:
            addresses = self._call(
                chain, "listaddressgroupings", wallet_name=wallet_name
            )
            if addresses and len(addresses) > 0:
                for group in addresses:
                    if group and len(group) > 0:
                        return group[0][0]
        except:
            pass

        return self._call(chain, "getnewaddress", "", wallet_name=wallet_name)

    def get_user_address(self, user_id: int, chain: str, user_guid: str = None) -> str:
        if user_guid:
            wallet_name = f"wallet_{user_guid}_{chain}"
        else:
            wallet_name = f"wallet_{user_id}_{chain}"
        return self._call(chain, "getnewaddress", "", wallet_name=wallet_name)

    def import_wif(
        self, user_id: int, chain: str, wif: str, passphrase: str = None
    ) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"

        if passphrase:
            result = self._call(
                chain,
                "importprivkey",
                wif,
                "",
                True,
                True,
                passphrase,
                wallet_name=wallet_name,
            )
        else:
            result = self._call(
                chain, "importprivkey", wif, "", True, wallet_name=wallet_name
            )

        return result

    def export_wif(self, user_id: int, chain: str) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"

        addresses = self._call(
            chain, "getaddressesbyaccount", wallet_name, wallet_name=wallet_name
        )
        if not addresses:
            return None

        address = addresses[0]
        result = self._call(chain, "dumpprivkey", address, wallet_name=wallet_name)
        return result

    def get_user_balance(self, user_id: int, chain: str) -> float:
        wallet_name = f"wallet_{user_id}_{chain}"
        return float(self._call(chain, "getbalance", "*", 0, wallet_name=wallet_name))

    def send_from_user(
        self, user_id: int, chain: str, to_address: str, amount: float
    ) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"
        result = self._call(
            chain, "sendtoaddress", to_address, amount, wallet_name=wallet_name
        )
        return result.get("txid") if isinstance(result, dict) else result

    def list_transactions(self, user_id: int, chain: str, count: int = 50) -> list:
        wallet_name = f"wallet_{user_id}_{chain}"
        return (
            self._call(
                chain, "listtransactions", "*", count, 0, wallet_name=wallet_name
            )
            or []
        )

    def backup_wallet(self, user_id: int, chain: str) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join("/data", "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"{wallet_name}_{timestamp}.dat")
        self._call(chain, "backupwallet", backup_path, wallet_name=wallet_name)
        return backup_path

    def encrypt_wallet(self, user_id: int, chain: str, passphrase: str):
        wallet_name = f"wallet_{user_id}_{chain}"
        return self._call(chain, "encryptwallet", passphrase, wallet_name=wallet_name)

    def change_wallet_passphrase(
        self, user_id: int, chain: str, old_pw: str, new_pw: str
    ):
        wallet_name = f"wallet_{user_id}_{chain}"
        return self._call(
            chain, "walletpassphrasechange", old_pw, new_pw, wallet_name=wallet_name
        )

    def get_blockchain_info(self, chain: str) -> dict:
        return self._call(chain, "getblockchaininfo")

    def get_network_info(self, chain: str) -> dict:
        return self._call(chain, "getnetworkinfo")

    def get_total_balance(self, chain: str) -> float:
        return float(self._call(chain, "getbalance", "*", 0))


from ordex_web_wallet.config import config

daemon_manager = DaemonManager(
    config.RPC_USER,
    config.RPC_PASS,
)


class CLIContext:
    """Legacy CLI-based context manager - kept for compatibility only."""

    def __init__(
        self,
        cli_path: str,
        chain: str,
        wallet_name: str = None,
        rpc_user: str = None,
        rpc_pass: str = None,
        rpc_port: int = None,
        data_dir: str = "/data",
        rpc_host: str = "127.0.0.1",
    ):
        import warnings

        warnings.warn(
            "CLIContext is deprecated. Use DaemonManager directly or HTTPRPCContext.",
            DeprecationWarning,
        )
        self.cli_path = cli_path
        self.chain = chain
        self.wallet_name = wallet_name
        self.rpc_user = rpc_user or os.getenv("RPC_USER", "ordex")
        self.rpc_pass = rpc_pass or os.getenv("RPC_PASS", "")
        self.rpc_port = rpc_port or (5332 if chain == "ordexcoin" else 5333)
        self.data_dir = data_dir
        self.rpc_host = rpc_host

    def call(self, method: str, *args) -> Any:
        import subprocess
        import re

        cmd = [
            self.cli_path,
            f"-rpcuser={self.rpc_user}",
            f"-rpcpassword={self.rpc_pass}",
            f"-rpcport={self.rpc_port}",
            f"-rpcconnect={self.rpc_host}",
            f"-datadir={self.data_dir}",
        ]
        if self.wallet_name and method != "loadwallet":
            cmd.append(f"-rpcwallet={self.wallet_name}")
        cmd.append(method)
        cmd.extend(str(arg) for arg in args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error = result.stderr.strip()
                rpc_code = -1
                rpc_message = error
                code_match = re.search(r"code\"?\s*:\s*(-?\d+)", error)
                if code_match:
                    rpc_code = int(code_match.group(1))
                raise RPCError(rpc_code, rpc_message)

            output = result.stdout.strip()
            if not output:
                return None
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
        except subprocess.TimeoutExpired:
            raise RPCError(-1, "RPC call timed out")
        except FileNotFoundError:
            raise RPCError(-1, f"CLI not found: {self.cli_path}")
