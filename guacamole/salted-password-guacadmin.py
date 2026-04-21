from hashlib import sha256
import os, binascii

password = "blahblahblah"

# 32 random bytes of salt
salt = os.urandom(32)
salt_hex = binascii.hexlify(salt).decode().upper()

# Guacamole hash: SHA256(password + SALT_HEX)
hash_hex = sha256((password + salt_hex).encode("utf-8")).hexdigest().upper()

print("Password:", password)
print("SALT_HEX:", salt_hex)
print("HASH_HEX:", hash_hex)
