import os
import argparse
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

def create_user(email, password):
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "password": password
    }
    response = httpx.post(url, headers=headers, json=data)
    print(f"Signup Status: {response.status_code}")
    print(response.json())
    if response.status_code == 200:
        print("\nNote: If 'email_not_confirmed' is the error upon login, you need to disable 'Confirm email' in Supabase Dashboard -> Auth -> Providers -> Email, or use a real email to confirm it.")

def login_user(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "password": password
    }
    response = httpx.post(url, headers=headers, json=data)
    print(f"Login Status: {response.status_code}")
    data = response.json()
    print(data)
    if response.status_code == 200:
        print("\n=== JWT Token ===")
        print(data.get("access_token"))
        print("=================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supabase Auth CLI")
    parser.add_argument("action", choices=["signup", "login"], help="Action to perform")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    
    args = parser.parse_args()
    if args.action == "signup":
        create_user(args.email, args.password)
    elif args.action == "login":
        login_user(args.email, args.password)
