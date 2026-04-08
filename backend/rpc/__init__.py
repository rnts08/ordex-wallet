"""
RPC Client Service for OrdexWallet.

Provides secure communication with ordexcoind and ordexgoldd daemons.
"""

import logging
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
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": list(args) if args else [],
            "id": 1,
        }

        timeout = kwargs.get("timeout", self.timeout)

        try:
            response = self.session.post(
                self.url,
                json=payload,
                auth=self._build_auth(),
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result and result["error"]:
                error = result["error"]
                raise RPCError(
                    code=error.get("code", -1),
                    message=error.get("message", "Unknown error"),
                )

            return result.get("result")

        except requests.exceptions.Timeout as e:
            logger.error(f"RPC timeout calling {method}: {e}")
            raise RPCConnectionError(f"Request timed out: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"RPC connection error calling {method}: {e}")
            raise RPCConnectionError(f"Connection failed: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"RPC HTTP error calling {method}: {e}")
            raise RPCConnectionError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"RPC request error calling {method}: {e}")
            raise RPCConnectionError(f"Request failed: {e}")

    def getinfo(self) -> Dict[str, Any]:
        return self.call("getinfo")

    def getblockcount(self) -> int:
        return self.call("getblockcount")

    def getbalance(self, account: str = "", minconf: int = 1) -> float:
        if account:
            return self.call("getbalance", account, minconf)
        return self.call("getbalance")

    def getnewaddress(self, account: str = "", address_type: str = "p2pkh") -> str:
        if account:
            return self.call("getnewaddress", account, address_type)
        return self.call("getnewaddress")

    def getaddressesbyaccount(self, account: str = "") -> List[str]:
        return self.call("getaddressesbyaccount", account)

    def getaccountaddress(self, account: str = "") -> str:
        return self.call("getaccountaddress", account)

    def validateaddress(self, address: str) -> Dict[str, Any]:
        return self.call("validateaddress", address)

    def listtransactions(
        self,
        account: str = "",
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
