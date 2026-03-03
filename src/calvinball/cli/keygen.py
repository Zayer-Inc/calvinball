"""RSA key pair generation for Snowflake key pair auth."""

from __future__ import annotations

import base64
from pathlib import Path


def generate_snowflake_keypair(output_dir: Path) -> tuple[Path, str]:
    """Generate an RSA 2048 key pair for Snowflake authentication.

    Returns (private_key_path, public_key_base64) where public_key_base64
    is suitable for the ``ALTER USER ... SET RSA_PUBLIC_KEY=`` statement.
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Serialize private key as unencrypted PKCS8 PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Write private key file with restrictive permissions
    output_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = output_dir / "snowflake_key.p8"
    private_key_path.write_bytes(private_pem)
    private_key_path.chmod(0o600)

    # Extract DER-encoded public key and base64-encode it
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_b64 = base64.b64encode(public_der).decode()

    return private_key_path, public_key_b64
