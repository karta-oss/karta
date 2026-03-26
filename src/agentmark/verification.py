"""Signature verification functionality for agentmark."""

import base64
import hashlib
import json
from typing import Any, Dict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature


def verify_signature(
    content: str,
    signature_data: Dict[str, Any],
    public_key_pem: str
) -> Dict[str, Any]:
    """
    Verify cryptographic signature of content.
    
    Args:
        content: Original content to verify
        signature_data: Output from sign_content()
        public_key_pem: RSA public key in PEM format
    
    Returns:
        {
            "valid": bool,
            "agent_id": str,
            "timestamp": float,
            "content_hash_matches": bool,
            "signature_valid": bool,
            "error": Optional[str]
        }
    
    Raises:
        ValueError: Invalid public key format
        TypeError: Malformed signature_data
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")
    
    if not isinstance(signature_data, dict):
        raise TypeError("signature_data must be a dictionary")
    
    if not isinstance(public_key_pem, str):
        raise ValueError("public_key_pem must be a string")
    
    # Initialize result with default values
    result = {
        "valid": False,
        "agent_id": signature_data.get("agent_id", ""),
        "timestamp": signature_data.get("timestamp", 0.0),
        "content_hash_matches": False,
        "signature_valid": False,
        "error": None
    }
    
    try:
        # Validate signature data structure
        required_fields = ["content_hash", "agent_id", "timestamp", "signature", "algorithm"]
        for field in required_fields:
            if field not in signature_data:
                result["error"] = f"Missing required field: {field}"
                return result
        
        # Verify algorithm
        if signature_data["algorithm"] != "RSA-SHA256":
            result["error"] = f"Unsupported algorithm: {signature_data['algorithm']}"
            return result
        
        # Compute content hash
        content_bytes = content.encode('utf-8')
        computed_hash = hashlib.sha256(content_bytes).hexdigest()
        
        # Check content hash matches
        stored_hash = signature_data["content_hash"]
        result["content_hash_matches"] = computed_hash == stored_hash
        
        if not result["content_hash_matches"]:
            result["error"] = "Content hash does not match stored hash"
            return result
        
        # Load public key
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
        except Exception as e:
            raise ValueError(f"Invalid public key format: {e}")
        
        # Verify it's an RSA key
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise ValueError("Public key must be RSA")
        
        # Decode signature
        try:
            signature_bytes = base64.b64decode(signature_data["signature"])
        except Exception as e:
            result["error"] = f"Invalid base64 signature: {e}"
            return result
        
        # Create message to verify (same format as signing)
        message_data = {
            "content_hash": stored_hash,
            "agent_id": signature_data["agent_id"],
            "timestamp": signature_data["timestamp"],
            "algorithm": signature_data["algorithm"]
        }
        message = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
        message_bytes = message.encode('utf-8')
        
        # Verify signature
        try:
            public_key.verify(
                signature_bytes,
                message_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            result["signature_valid"] = True
        except InvalidSignature:
            result["error"] = "Signature verification failed"
            return result
        except Exception as e:
            result["error"] = f"Signature verification error: {e}"
            return result
        
        # All checks passed
        result["valid"] = True
        return result
        
    except Exception as e:
        if "error" not in result or result["error"] is None:
            result["error"] = str(e)
        return result
