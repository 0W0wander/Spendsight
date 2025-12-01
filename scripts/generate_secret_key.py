#!/usr/bin/env python3
"""
Generate a random secret key for Flask
"""
import secrets

if __name__ == '__main__':
    secret_key = secrets.token_hex(32)
    print("Generated Flask Secret Key:")
    print("=" * 70)
    print(secret_key)
    print("=" * 70)
    print("\nCopy this to your .env file as FLASK_SECRET_KEY=<key>")

