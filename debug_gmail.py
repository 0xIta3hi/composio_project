import os
from composio import Composio

# --- CONFIGURATION ---
os.environ["COMPOSIO_API_KEY"] = "ak_GiG5fj7cc1S7h3V9MBxc"

composio = Composio(api_key=os.environ["COMPOSIO_API_KEY"])

print("=" * 60)
print("DEBUGGING GMAIL CONNECTION")
print("=" * 60)

# Test 1: Try to list connected integrations
print("\n1. Checking connected integrations on Composio platform...")
try:
    # Try to get integrations/connections
    response = composio.client.get("/integrations")
    print(f"Integrations: {response}")
except Exception as e:
    print(f"   Info: {e}")

# Test 2: Try different user IDs
user_ids_to_test = ["default", "me", "user", ""]

for user_id in user_ids_to_test:
    print(f"\n2. Testing with user_id='{user_id}'...")
    try:
        tools = composio.tools.get(
            user_id=user_id if user_id else None,
            toolkits=["gmail"]
        )
        if tools:
            print(f"   ✅ Found {len(tools)} Gmail tools!")
            print(f"   Sample tools:")
            for i, tool in enumerate(tools[:3]):
                if isinstance(tool, dict) and 'function' in tool:
                    name = tool['function'].get('name', 'Unknown')
                    print(f"      - {name}")
            break
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

# Test 3: Check what the actual connected user email is
print(f"\n3. Looking for email-based user IDs...")
try:
    # Sometimes the user_id is the email address that was authenticated
    response = composio.client.get("/v1/user")
    print(f"   Current user: {response}")
except Exception as e:
    print(f"   Info: {e}")

print("\n" + "=" * 60)
print("INSTRUCTIONS:")
print("=" * 60)
print("1. Go to {{COMPOSIO_DASHBOARD}}")
print("2. Find your Gmail connection")
print("3. Use the exact User ID/Email shown there in the script")
print("4. Update gmail_auth.py with: setup_gmail_account(composio, user_id='YOUR_EMAIL_OR_ID')")
print("=" * 60)
