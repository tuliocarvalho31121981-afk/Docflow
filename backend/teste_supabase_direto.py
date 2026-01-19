"""Teste direto de autenticação com Supabase"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:20]}..." if key else "Key: None")

client = create_client(url, key)

try:
    response = client.auth.sign_in_with_password({
        "email": "tuliocarvalho31121981@gmail.com",
        "password": "aloha123"
    })
    print("\n✓ LOGIN OK!")
    print(f"User ID: {response.user.id}")
    print(f"Access Token: {response.session.access_token[:50]}...")
except Exception as e:
    print(f"\n✗ ERRO: {e}")
