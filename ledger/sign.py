"""Optional Ed25519 root signing.

The per-line checksum is an integrity mark, not a signature (README limit 2).
This module closes that gap at the ROOT: one signature over the tip root
covers every entry by induction through the chain.

Dependency: `cryptography` (pip). The ledger core stays stdlib-only; signing
is an option, and the pins skip — never silently pass — when it is absent.
"""
import os

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    HAVE_CRYPTO = True
except ImportError:  # pragma: no cover — environment without cryptography
    HAVE_CRYPTO = False


def _need():
    if not HAVE_CRYPTO:
        raise RuntimeError("ledger.sign requires the 'cryptography' package "
                           "— the append-only core works without it")


def generate_keypair():
    """fresh keypair -> (private_pem_bytes, public_pem_bytes)"""
    _need()
    priv = Ed25519PrivateKey.generate()
    return (priv.private_bytes(serialization.Encoding.PEM,
                               serialization.PrivateFormat.PKCS8,
                               serialization.NoEncryption()),
            priv.public_key().public_bytes(serialization.Encoding.PEM,
                                           serialization.PublicFormat.SubjectPublicKeyInfo))


def sign_root(root_hex, private_pem):
    """Sign a root hash (from ledger.export.root_hash). Returns 64 raw bytes."""
    _need()
    if not isinstance(root_hex, str) or len(root_hex) != 16:
        raise ValueError(f"root must be a 16-hex-char fnv1a-64 tip, got {root_hex!r}")
    priv = serialization.load_pem_private_key(private_pem, password=None)
    return priv.sign(root_hex.encode("ascii"))


def verify_root(root_hex, public_pem, signature):
    """True iff public key validates this signature over this exact root."""
    _need()
    pub = serialization.load_pem_public_key(public_pem)
    if not isinstance(pub, Ed25519PublicKey):
        raise ValueError("not an Ed25519 public key")
    try:
        pub.verify(signature, root_hex.encode("ascii"))
        return True
    except InvalidSignature:
        return False
    except (ValueError, TypeError):
        return False


def save_keypair(dirpath, prefix="ledger"):
    """Convenience: write keypair files, mode 0600 on the private half."""
    _need()
    os.makedirs(dirpath, exist_ok=True)
    priv, pub = generate_keypair()
    p = os.path.join(dirpath, f"{prefix}.key")
    q = os.path.join(dirpath, f"{prefix}.pub")
    with open(p, "wb") as f:
        f.write(priv)
    with open(q, "wb") as f:
        f.write(pub)
    os.chmod(p, 0o600)
    return p, q
