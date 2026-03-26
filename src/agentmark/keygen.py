"""Key pair generation functionality for agentmark."""

import os
import re
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_keypair(agent_id: str) -> Tuple[str, str]:
    """Generate RSA-2048 key pair for agent.
    
    Args:
        agent_id: Unique agent identifier
    
    Returns:
        (private_key_pem, public_key_pem)
    
    Raises:
        ValueError: Invalid agent_id format (must be [a-zA-Z0-9_-]+)
    """
    if not isinstance(agent_id, str):
        raise ValueError("agent_id must be a string")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id) or len(agent_id) == 0 or len(agent_id) > 64:
        raise ValueError("agent_id must match [a-zA-Z0-9_-]{1,64}")
    
    # Generate RSA-2048 key pair using cryptographically secure randomness
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Serialize public key to PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def save_keypair(agent_id: str, private_key_pem: str, public_key_pem: str, output_dir: str = ".", force: bool = False) -> Tuple[str, str]:
    """Save key pair to PEM files with agent ID in filename.
    
    Args:
        agent_id: Unique agent identifier
        private_key_pem: Private key in PEM format
        public_key_pem: Public key in PEM format
        output_dir: Directory to save keys (default: current directory)
        force: Skip confirmation for overwriting existing files
    
    Returns:
        (private_key_path, public_key_path)
    
    Raises:
        FileExistsError: Key files already exist and force=False
        OSError: Cannot write to output directory
    """
    private_key_path = os.path.join(output_dir, f"{agent_id}.private.pem")
    public_key_path = os.path.join(output_dir, f"{agent_id}.public.pem")
    
    # Check if files already exist
    if not force and (os.path.exists(private_key_path) or os.path.exists(public_key_path)):
        raise FileExistsError(f"Key files for {agent_id} already exist. Use --force to overwrite.")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write private key
    with open(private_key_path, 'w') as f:
        f.write(private_key_pem)
    
    # Write public key
    with open(public_key_path, 'w') as f:
        f.write(public_key_pem)
    
    # Set restrictive permissions on private key file
    os.chmod(private_key_path, 0o600)
    
    return private_key_path, public_key_path