import os
import subprocess
import json
from typing import Any, Optional


class RPCError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RPC Error {code}: {message}")


CLI_PATH = os.getenv("CLI_PATH", "/usr/local/bin")


class CLIContext:
    """Context manager for running CLI commands with proper wallet isolation."""

    def __init__(
        self,
        cli_path: str,
        chain: str,
        wallet_name: str = None,
        rpc_user: str = None,
        rpc_pass: str = None,
        rpc_port: int = None,
        data_dir: str = "/data",
    ):
        self.cli_path = cli_path
        self.chain = chain
        self.wallet_name = wallet_name
        self.rpc_user = rpc_user or os.getenv("RPC_USER", "ordex")
        self.rpc_pass = rpc_pass or os.getenv("RPC_PASS", "")
        self.rpc_port = rpc_port or (5332 if chain == "ordexcoin" else 5333)
        self.data_dir = data_dir

    def _build_cmd(self, method: str, *args) -> list:
        cmd = [
            self.cli_path,
            f"-rpcuser={self.rpc_user}",
            f"-rpcpassword={self.rpc_pass}",
            f"-rpcport={self.rpc_port}",
            f"-datadir={self.data_dir}",
        ]
        if self.wallet_name:
            cmd.append(f"-rpcwallet={self.wallet_name}")
        cmd.append(method)
        cmd.extend(str(arg) for arg in args)
        return cmd

    def call(self, method: str, *args) -> Any:
        cmd = self._build_cmd(method, *args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                error = result.stderr.strip()
                if "error:" in error.lower():
                    parts = error.split("error message:")
                    if len(parts) > 1:
                        raise RPCError(-1, parts[1].strip())
                    raise RPCError(-1, error)
                raise RPCError(result.returncode, error)

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


class DaemonManager:
    def __init__(
        self, cli_path: str, rpc_user: str, rpc_pass: str, data_dir: str = "/data"
    ):
        self.cli_path = cli_path
        self.rpc_user = rpc_user
        self.rpc_pass = rpc_pass
        self.data_dir = data_dir
        self.oxc_port = int(os.getenv("OXRPC_PORT", "5332"))
        self.oxg_port = int(os.getenv("OGRPC_PORT", "5333"))

    def get_context(self, chain: str, wallet_name: str = None) -> CLIContext:
        port = self.oxc_port if chain == "ordexcoin" else self.oxg_port
        return CLIContext(
            self.cli_path,
            chain,
            wallet_name,
            self.rpc_user,
            self.rpc_pass,
            port,
        )

    def create_user_wallet(
        self, user_id: int, chain: str, passphrase: str = None
    ) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"
        ctx = self.get_context(chain)

        result = ctx.call("createwallet", wallet_name)
        # Note: encryption requires separate step - skip for now
        _ = result  # Acknowledge result

        return wallet_name

    def get_user_address(self, user_id: int, chain: str) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"
        ctx = self.get_context(chain, wallet_name)
        return ctx.call("getnewaddress", "")

    def get_user_balance(self, user_id: int, chain: str) -> float:
        wallet_name = f"wallet_{user_id}_{chain}"
        ctx = self.get_context(chain, wallet_name)
        return float(ctx.call("getbalance", "*", 0))

    def send_from_user(
        self, user_id: int, chain: str, to_address: str, amount: float
    ) -> str:
        wallet_name = f"wallet_{user_id}_{chain}"
        ctx = self.get_context(chain, wallet_name)
        result = ctx.call("sendtoaddress", to_address, amount)
        return result.get("txid") if result else None

    def list_transactions(self, user_id: int, chain: str, count: int = 50) -> list:
        wallet_name = f"wallet_{user_id}_{chain}"
        ctx = self.get_context(chain, wallet_name)
        return ctx.call("listtransactions", "*", count, 0) or []

    def get_blockchain_info(self, chain: str) -> dict:
        ctx = self.get_context(chain)
        return ctx.call("getblockchaininfo")

    def get_network_info(self, chain: str) -> dict:
        ctx = self.get_context(chain)
        return ctx.call("getnetworkinfo")


def _get_default_cli_path(chain: str) -> str:
    bin_dir = os.getenv("BIN_DIR", "/app/bin")
    if chain == "ordexcoin":
        return os.path.join(bin_dir, "ordexcoin-cli")
    return os.path.join(bin_dir, "ordexgold-cli")


from ordex_web_wallet.config import config

daemon_manager = DaemonManager(
    _get_default_cli_path("ordexcoin"),
    config.RPC_USER,
    config.RPC_PASS,
)


class RPCClient:
    """HTTP-based RPC client (kept for compatibility)."""

    def __init__(self, url: str, user: str, password: str):
        self.url = url
        self.auth = (user, password)

    def call(self, method: str, *args) -> Any:
        import requests

        payload = {"method": method, "params": list(args), "id": 1}
        response = requests.post(
            self.url,
            json=payload,
            auth=self.auth,
            timeout=30,
        )
        result = response.json()
        if result.get("error"):
            error = result["error"]
            raise RPCError(error.get("code", -1), error.get("message", "Unknown"))
        return result.get("result")
