import json
import os
import main
import config

def test_load_clients():
    print("Testing load_clients...")
    clients = main.load_clients()
    if not clients:
        print("FAILED: No clients loaded.")
        return False
    print(f"SUCCESS: Loaded {len(clients)} clients.")
    for c in clients:
        print(f"  - {c['client_name']} ({c['client_id']})")
    return True

def test_config_sharing():
    print("Testing shared config...")
    if not config.GMAIL_USER or not config.GMAIL_PASS:
        print("FAILED: GMAIL credentials missing in config.py")
        return False
    print(f"SUCCESS: Found credentials for {config.GMAIL_USER}")
    return True

if __name__ == "__main__":
    s1 = test_load_clients()
    s2 = test_config_sharing()
    if s1 and s2:
        print("\nCore logic verification PASSED.")
    else:
        print("\nCore logic verification FAILED.")
