"""Core cryptographic signing functionality for agentmark."""

import base64
import hashlib
import json
import time
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def sign_content(
    content: str,
    agent_id: str,
    private_key_pem: str,
    timestamp: Optional[float] = None
) -> Dict[str, Any]:
    """
    Sign content with cryptographic signature.
    
    Args:
        content: The code or text to sign
        agent_id: Unique identifier for the signing agent
        private_key_pem: RSA private key in PEM format
        timestamp: Unix timestamp (defaults to time.time())
    
    Returns:
        {
            "content_hash": str,  # SHA-256 hex digest
            "agent_id": str,
            "timestamp": float,
            "signature": str,     # Base64-encoded RSA signature
            "algorithm": "RSA-SHA256"
        }
    
    Raises:
        ValueError: Invalid private key or agent_id format
        TypeError: content is not string
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")
    
    # Validate agent_id format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', agent_id):
        raise ValueError("agent_id must match pattern [a-zA-Z0-9_-]{1,64}")
    
    # Use provided timestamp or current time
    if timestamp is None:
        timestamp = time.time()
    
    # Calculate content hash
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    # Load private key
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )
    except Exception as e:
        raise ValueError(f"Invalid private key format: {e}")
    
    # Create message to sign (deterministic)
    message_data = {
        "content_hash": content_hash,
        "agent_id": agent_id,
        "timestamp": timestamp,
        "algorithm": "RSA-SHA256"
    }
    
    # Convert to canonical JSON for signing
    message_json = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
    message_bytes = message_json.encode('utf-8')
    
    # Sign the message
    try:
        signature_bytes = private_key.sign(
            message_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except Exception as e:
        raise ValueError(f"Signing failed: {e}")
    
    # Encode signature as base64
    signature_b64 = base64.b64encode(signature_bytes).decode('ascii')
    
    # Return signature data
    return {
        "content_hash": content_hash,
        "agent_id": agent_id,
        "timestamp": timestamp,
        "signature": signature_b64,
        "algorithm": "RSA-SHA256"
    }
