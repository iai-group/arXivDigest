#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate secure JWT and secret keys for arXivDigest configuration."""

import json
import secrets
import string

def generate_jwt_key(length=128):
    """Generate a secure JWT key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secret_key(length=128):
    """Generate a secure secret key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    jwt_key = generate_jwt_key()
    secret_key = generate_secret_key()
    
    print("Generated Keys for arXivDigest Configuration")
    print("=" * 60)
    print("\nAdd these to your config.json under 'frontend_config':\n")
    print(json.dumps({"jwt_key": jwt_key, "secret_key": secret_key}, indent=2)[1:-1])
    print("\n" + "=" * 60)
    print("\nIMPORTANT: Keep these keys secret and secure!")
    print("Do not commit them to version control.")
