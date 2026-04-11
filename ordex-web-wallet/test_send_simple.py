#!/usr/bin/env python3

import os
import sys

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)


def test_send_endpoint_structure():
    """Test that the send endpoint exists and has correct structure."""
    # Import the app
    from ordex_web_wallet.app import create_app

    # Create app instance
    app = create_app()
    app.config["TESTING"] = True

    # Check that the send route exists
    with app.test_client() as client:
        # We can't easily test the actual endpoint without complex mocking
        # but we can verify the route is registered
        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            if "send" in rule.rule:
                print(f"  {rule.rule} -> {rule.endpoint} ({', '.join(rule.methods)})")

        # Specifically check for wallet send endpoint
        send_rules = [r for r in app.url_map.iter_rules() if "wallet/send" in r.rule]
        assert len(send_rules) > 0, "Wallet send endpoint not found"
        send_rule = send_rules[0]
        assert "POST" in send_rule.methods, "Wallet send endpoint should accept POST"

        print(f"✓ Found wallet send endpoint: {send_rule.rule}")
        print(f"✓ Accepts methods: {', '.join(send_rule.methods)}")


if __name__ == "__main__":
    test_send_endpoint_structure()
    print("All tests passed!")
