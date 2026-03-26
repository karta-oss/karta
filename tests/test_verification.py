"""Tests for signature verification functionality."""

import base64
import hashlib
import json
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from agentmark.verification import verify_signature


def generate_test_keypair():
    """Generate a test RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_key, private_pem, public_pem


def create_test_signature(content: str, agent_id: str, private_key, timestamp: float = 1234567890.0):
    """Create a test signature using the same method as the signing function would."""
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    message_data = {
        "content_hash": content_hash,
        "agent_id": agent_id,
        "timestamp": timestamp,
        "algorithm": "RSA-SHA256"
    }
    
    message = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
    message_bytes = message.encode('utf-8')
    
    signature_bytes = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
    
    return {
        "content_hash": content_hash,
        "agent_id": agent_id,
        "timestamp": timestamp,
        "signature": signature_b64,
        "algorithm": "RSA-SHA256"
    }


class TestVerifySignature:
    def test_valid_signature(self):
        """Test verification of a valid signature."""
        private_key, private_pem, public_pem = generate_test_keypair()
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key)
        
        result = verify_signature(content, signature_data, public_pem)
        
        assert result["valid"] is True
        assert result["agent_id"] == agent_id
        assert result["timestamp"] == 1234567890.0
        assert result["content_hash_matches"] is True
        assert result["signature_valid"] is True
        assert result["error"] is None
    
    def test_invalid_content_hash(self):
        """Test verification with modified content."""
        private_key, private_pem, public_pem = generate_test_keypair()
        original_content = "print('Hello, World!')"
        modified_content = "print('Hello, Universe!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(original_content, agent_id, private_key)
        
        result = verify_signature(modified_content, signature_data, public_pem)
        
        assert result["valid"] is False
        assert result["content_hash_matches"] is False
        assert result["signature_valid"] is False
        assert "Content hash does not match" in result["error"]
    
    def test_invalid_signature(self):
        """Test verification with tampered signature."""
        private_key, private_pem, public_pem = generate_test_keypair()
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key)
        
        # Tamper with signature
        signature_data["signature"] = "invalid-signature"
        
        result = verify_signature(content, signature_data, public_pem)
        
        assert result["valid"] is False
        assert "Invalid base64 signature" in result["error"]
    
    def test_wrong_public_key(self):
        """Test verification with wrong public key."""
        private_key1, _, _ = generate_test_keypair()
        _, _, public_pem2 = generate_test_keypair()
        
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key1)
        
        result = verify_signature(content, signature_data, public_pem2)
        
        assert result["valid"] is False
        assert result["content_hash_matches"] is True
        assert result["signature_valid"] is False
        assert "Signature verification failed" in result["error"]
    
    def test_missing_required_fields(self):
        """Test verification with missing signature data fields."""
        _, _, public_pem = generate_test_keypair()
        content = "print('Hello, World!')"
        
        incomplete_signature = {
            "content_hash": "some-hash",
            "agent_id": "test-agent"
            # Missing timestamp, signature, algorithm
        }
        
        result = verify_signature(content, incomplete_signature, public_pem)
        
        assert result["valid"] is False
        assert "Missing required field: timestamp" in result["error"]
    
    def test_unsupported_algorithm(self):
        """Test verification with unsupported algorithm."""
        private_key, _, public_pem = generate_test_keypair()
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key)
        signature_data["algorithm"] = "INVALID-ALGO"
        
        result = verify_signature(content, signature_data, public_pem)
        
        assert result["valid"] is False
        assert "Unsupported algorithm: INVALID-ALGO" in result["error"]
    
    def test_invalid_public_key(self):
        """Test verification with invalid public key."""
        private_key, _, _ = generate_test_keypair()
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key)
        
        with pytest.raises(ValueError, match="Invalid public key format"):
            verify_signature(content, signature_data, "invalid-key")
    
    def test_type_errors(self):
        """Test type validation for inputs."""
        _, _, public_pem = generate_test_keypair()
        
        # Test non-string content
        with pytest.raises(TypeError, match="content must be a string"):
            verify_signature(123, {}, public_pem)
        
        # Test non-dict signature_data
        with pytest.raises(TypeError, match="signature_data must be a dictionary"):
            verify_signature("content", "not-dict", public_pem)
        
        # Test non-string public key
        with pytest.raises(ValueError, match="public_key_pem must be a string"):
            verify_signature("content", {}, 123)
    
    def test_corrupted_signature_base64(self):
        """Test verification with corrupted base64 signature."""
        private_key, _, public_pem = generate_test_keypair()
        content = "print('Hello, World!')"
        agent_id = "test-agent"
        
        signature_data = create_test_signature(content, agent_id, private_key)
        
        # Create invalid base64
        original_sig = signature_data["signature"]
        signature_data["signature"] = original_sig[:-4] + "!!!!"
        
        result = verify_signature(content, signature_data, public_pem)
        
        assert result["valid"] is False
        assert "Invalid base64 signature" in result["error"]
