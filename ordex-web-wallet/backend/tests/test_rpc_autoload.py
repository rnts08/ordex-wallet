import pytest
from unittest.mock import patch, MagicMock
from ordex_web_wallet.rpc import CLIContext, RPCError

def test_cli_context_autoload_retry():
    """Test that CLIContext.call retries after loading wallet on Error -18."""
    
    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        # Mock 1: First call returns Error -18 (Wallet not found)
        # Mock 2: loadwallet call returns Success
        # Mock 3: Original call retry returns Success
        
        mock_resp_fail = MagicMock()
        mock_resp_fail.returncode = 1
        mock_resp_fail.stderr = "error code: -18, error message: wallet not found"
        mock_resp_fail.stdout = ""
        
        mock_resp_success = MagicMock()
        mock_resp_success.returncode = 0
        mock_resp_success.stdout = '{"result": "success"}'
        mock_resp_success.stderr = ""
        
        mock_run.side_effect = [mock_resp_fail, mock_resp_success, mock_resp_success]
        
        ctx = CLIContext(cli_path="cli", chain="ordexcoin", wallet_name="testwallet")
        result = ctx.call("getbalance")
        
        assert result == {"result": "success"}
        assert mock_run.call_count == 3
        # First call: getbalance
        # Second call: loadwallet
        # Third call: getbalance (retry)
        
        args_list = [call.args[0] for call in mock_run.call_args_list]
        assert "getbalance" in args_list[0]
        assert "loadwallet" in args_list[1]
        assert "getbalance" in args_list[2]

def test_cli_context_autoload_failure():
    """Test that CLIContext.call raises original error if loadwallet fails."""
    
    with patch("subprocess.run") as mock_run:
        mock_resp_fail = MagicMock()
        mock_resp_fail.returncode = 1
        mock_resp_fail.stderr = "error code: -18, error message: wallet not found"
        
        mock_resp_load_fail = MagicMock()
        mock_resp_load_fail.returncode = 1
        mock_resp_load_fail.stderr = "error code: -1, error message: file not found"
        
        mock_run.side_effect = [mock_resp_fail, mock_resp_load_fail]
        
        ctx = CLIContext(cli_path="cli", chain="ordexcoin", wallet_name="testwallet")
        
        with pytest.raises(RPCError) as excinfo:
            ctx.call("getbalance")
        
        assert excinfo.value.code == -18
        assert mock_run.call_count == 2

def test_cli_context_json_error_parsing():
    """Test that CLIContext can parse Error -18 from JSON-style output."""
    
    with patch("subprocess.run") as mock_run:
        mock_resp_json = MagicMock()
        mock_resp_json.returncode = 1
        # JSON output without space after colon
        mock_resp_json.stderr = 'error: {"code":-18,"message":"Requested wallet does not exist"}'
        mock_resp_json.stdout = ""
        
        mock_resp_success = MagicMock()
        mock_resp_success.returncode = 0
        mock_resp_success.stdout = '{"result": "success"}'
        
        mock_run.side_effect = [mock_resp_json, mock_resp_success, mock_resp_success]
        
        ctx = CLIContext(cli_path="cli", chain="ordexcoin", wallet_name="testwallet")
        result = ctx.call("getbalance")
        
        assert result == {"result": "success"}
        assert mock_run.call_count == 3
