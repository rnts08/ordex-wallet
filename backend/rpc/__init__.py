"""
RPC Client Service for OrdexWallet.

Provides secure communication with ordexcoind and ordexgoldd daemons.
"""

import logging
import json
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class RPCError(Exception):
    """Exception raised when RPC call returns an error."""

    code: int
    message: str

    def __str__(self):
        return f"RPC Error {self.code}: {self.message}"


@dataclass
class RPCConnectionError(Exception):
    """Exception raised when RPC connection fails."""

    message: str

    def __str__(self):
        return f"Connection Error: {self.message}"


class OrdexRPCClient:
    """JSON-RPC client for Ordex network daemons."""

    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 5
    RETRY_BACKOFF_FACTOR = 2

    def __init__(
        self,
        host: str = "localhost",
        port: int = 25173,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        daemon_name: str = "ordexcoind",
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.daemon_name = daemon_name
        self.url = f"http://{host}:{port}"

        self.session = requests.Session()

        # Debug: log session settings
        logger.debug(f"RPC session created for {self.daemon_name}")

        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF_FACTOR,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized {daemon_name} RPC client: {self.url}")

    def _build_auth(self) -> Optional[tuple]:
        if self.user and self.password:
            return (self.user, self.password)
        return None

    def call(self, method: str, *args, **kwargs) -> Any:
        import socket
        import base64

        payload = {
            "jsonrpc": "1.0",
            "method": method,
            "params": list(args) if args else [],
            "id": 1,
        }

        timeout = kwargs.get("timeout", self.timeout)

        logger.info(f"RPC call: {self.daemon_name} {method}")

        body = json.dumps(payload)

        last_error = None
        for attempt in range(5):
            try:
                # Create socket connection directly
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((self.host, self.port))

                # Build HTTP request manually
                auth_str = base64.b64encode(
                    f"{self.user}:{self.password}".encode()
                ).decode()
                request = f"POST / HTTP/1.1\r\nHost: {self.host}\r\nAuthorization: Basic {auth_str}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n{body}"

                sock.send(request.encode())

                # Read response
                response = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    # Check if we have complete response (has double newline and content-length if POST)
                    if b"\r\n\r\n" in response:
                        break

                sock.close()

                # Parse HTTP response
                if not response:
                    raise RPCConnectionError("Empty response")

                # Extract body after headers
                body_start = response.find(b"\r\n\r\n")
                if body_start == -1:
                    raise RPCConnectionError("Invalid response format")

                body_str = response[body_start + 4 :].decode()

                # Parse JSON
                result = json.loads(body_str)

                if "error" in result and result["error"]:
                    raise RPCError(
                        code=result["error"].get("code", -1),
                        message=result["error"].get("message", "Unknown error"),
                    )

                return result.get("result")

            except Exception as e:
                last_error = e
                if attempt < 4:
                    logger.warning(
                        f"RPC attempt {attempt + 1} failed for {method}, retrying: {e}"
                    )
                    import time

                    time.sleep(2 * (attempt + 1))
                    continue
                break

        # All attempts failed
        logger.error(f"RPC error calling {method} after 5 attempts: {last_error}")
        raise RPCConnectionError(f"Request failed: {last_error}")

    def getinfo(self) -> Dict[str, Any]:
        return self.call("getblockchaininfo")

    def getblockchaininfo(self) -> Dict[str, Any]:
        return self.call("getblockchaininfo")

    def getblockcount(self) -> int:
        return self.call("getblockcount")

    def getwalletinfo(self) -> Dict[str, Any]:
        return self.call("getwalletinfo")

    def listwallets(self) -> List[str]:
        return self.call("listwallets")

    def loadwallet(self, name: str) -> Dict[str, Any]:
        return self.call("loadwallet", name)

    def createwallet(self, name: str) -> Dict[str, Any]:
        return self.call("createwallet", name)

    def getbalance(self, account: str = "", minconf: int = 1) -> float:
        if account:
            return self.call("getbalance", account, minconf)
        return self.call("getbalance")

    def getnewaddress(self, account: str = "", address_type: str = "bech32") -> str:
        if account:
            return self.call("getnewaddress", account, address_type)
        return self.call("getnewaddress")

    def getaddressbyaccount(self, account: str = "") -> str:
        return self.call("getaddressbyaccount", account)

    def validateaddress(self, address: str) -> Dict[str, Any]:
        return self.call("validateaddress", address)

    def listreceivedbyaddress(
        self,
        minconf: int = 1,
        include_empty: bool = False,
        include_watchonly: bool = False,
    ) -> List[Dict[str, Any]]:
        return self.call(
            "listreceivedbyaddress", minconf, include_empty, include_watchonly
        )

    def listtransactions(
        self,
        account: str = "*",
        count: int = 10,
        skip: int = 0,
        include_watchonly: bool = False,
    ) -> List[Dict[str, Any]]:
        return self.call("listtransactions", account, count, skip, include_watchonly)

    def listunspent(
        self,
        minconf: int = 1,
        maxconf: int = 999999,
        addresses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if addresses:
            return self.call("listunspent", minconf, maxconf, addresses)
        return self.call("listunspent", minconf, maxconf)

    def gettransaction(self, txid: str) -> Dict[str, Any]:
        return self.call("gettransaction", txid)

    def createrawtransaction(
        self, inputs: List[Dict[str, Any]], outputs: Dict[str, float]
    ) -> str:
        return self.call("createrawtransaction", inputs, outputs)

    def signrawtransaction(
        self,
        hexstring: str,
        prevtxs: Optional[List[Dict[str, Any]]] = None,
        privkeys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self.call("signrawtransaction", hexstring, prevtxs or [], privkeys or [])

    def sendrawtransaction(self, hexstring: str, allow_high_fees: bool = False) -> str:
        return self.call("sendrawtransaction", hexstring, allow_high_fees)

    def getblockhash(self, height: int) -> str:
        return self.call("getblockhash", height)

    def getblock(self, block_hash: str, verbose: bool = True) -> Dict[str, Any]:
        return self.call("getblock", block_hash, verbose)

    def getrawtransaction(
        self,
        txid: str,
        verbose: bool = False,
        block_hash: Optional[str] = None,
    ) -> Union[str, Dict[str, Any]]:
        if block_hash:
            return self.call("getrawtransaction", txid, verbose, block_hash)
        return self.call("getrawtransaction", txid, verbose)

    def gettxout(
        self, txid: str, n: int, include_mempool: bool = True
    ) -> Optional[Dict[str, Any]]:
        return self.call("gettxout", txid, n, include_mempool)

    def estimatefee(self, nblocks: int = 6) -> float:
        return self.call("estimatefee", nblocks)

    def estimatepriority(self, nblocks: int = 6) -> float:
        return self.call("estimatepriority", nblocks)

    def signmessage(self, address: str, message: str) -> str:
        return self.call("signmessage", address, message)

    def verifymessage(self, address: str, signature: str, message: str) -> bool:
        return self.call("verifymessage", address, signature, message)

    def dumpprivkey(self, address: str) -> str:
        return self.call("dumpprivkey", address)

    def importprivkey(self, privkey: str, label: str = "", rescan: bool = True) -> None:
        self.call("importprivkey", privkey, label, rescan)

    def walletpassphrase(self, passphrase: str, timeout: int) -> None:
        self.call("walletpassphrase", passphrase, timeout)

    def walletlock(self) -> None:
        self.call("walletlock")

    def getnetworkinfo(self) -> Dict[str, Any]:
        return self.call("getnetworkinfo")

    def getpeerinfo(self) -> List[Dict[str, Any]]:
        return self.call("getpeerinfo")

    def getmempoolinfo(self) -> Dict[str, Any]:
        return self.call("getmempoolinfo")

    def ping(self) -> None:
        return self.call("ping")

    def is_connected(self) -> bool:
        try:
            self.ping()
            return True
        except Exception:
            return False

    def get_sync_status(self) -> Dict[str, Any]:
        try:
            info = self.getinfo()
            return {
                "connected": True,
                "blocks": info.get("blocks", 0),
                "headers": info.get("headers", 0),
                "syncing": info.get("blocks", 0) < info.get("headers", 0),
                "verificationprogress": info.get("verificationprogress", 0),
                "difficulty": info.get("difficulty", 0),
                "size_on_disk": info.get("size_on_disk", 0),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }


class OrdexCoinClient(OrdexRPCClient):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 25173,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__(host, port, user, password, daemon_name="ordexcoind")


class OrdexGoldClient(OrdexRPCClient):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 25466,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__(host, port, user, password, daemon_name="ordexgoldd")


class RPCClientManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        daemons = config.get("daemons", {})

        ordexcoind = daemons.get("ordexcoind", {})
        self.ordexcoind = OrdexCoinClient(
            host=ordexcoind.get("host", "localhost"),
            port=ordexcoind.get("port", 25173),
            user=ordexcoind.get("username"),
            password=ordexcoind.get("password"),
        )

        ordexgoldd = daemons.get("ordexgoldd", {})
        self.ordexgoldd = OrdexGoldClient(
            host=ordexgoldd.get("host", "localhost"),
            port=ordexgoldd.get("port", 25466),
            user=ordexgoldd.get("username"),
            password=ordexgoldd.get("password"),
        )

        logger.info("RPC Client Manager initialized")

    def get_client(self, daemon: str) -> OrdexRPCClient:
        if daemon == "ordexcoind":
            return self.ordexcoind
        elif daemon == "ordexgoldd":
            return self.ordexgoldd
        else:
            raise ValueError(f"Unknown daemon: {daemon}")

    def get_sync_status(self) -> Dict[str, Any]:
        return {
            "ordexcoind": self.ordexcoind.get_sync_status(),
            "ordexgoldd": self.ordexgoldd.get_sync_status(),
        }

    def is_connected(self) -> bool:
        return self.ordexcoind.is_connected() and self.ordexgoldd.is_connected()
