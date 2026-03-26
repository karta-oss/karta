"""Tests for the signing module."""

import json
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from agentmark.signing import sign_content


@pytest.fixture
def test_keypair():
    """Generate a test RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def test_sign_content_basic(test_keypair):
    """Test basic content signing functionality."""
    private_key, _ = test_keypair
    
    content = "print('Hello, world!')"
    agent_id = "test-agent-1"
    timestamp = 1640995200.0  # Fixed timestamp for deterministic testing
    
    result = sign_content(content, agent_id, private_key, timestamp)
    
    # Check structure
    assert isinstance(result, dict)
    assert "content_hash" in result
    assert "agent_id" in result
    assert "timestamp" in result
    assert "signature" in result
    assert "algorithm" in result
    
    # Check values
    assert result["agent_id"] == agent_id
    assert result["timestamp"] == timestamp
    assert result["algorithm"] == "RSA-SHA256"
    
    # Check content hash is correct SHA-256
    import hashlib
    expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    assert result["content_hash"] == expected_hash
    
    # Check signature is base64
    import base64
    try:
        base64.b64decode(result["signature"])
    except Exception:
        pytest.fail("Signature is not valid base64")


def test_sign_content_deterministic(test_keypair):
    """Test that signing is deterministic for same inputs."""
    private_key, _ = test_keypair
    
    content = "def hello(): return 'world'"
    agent_id = "deterministic-agent"
    timestamp = 1640995200.123
    
    # Sign twice with same inputs
    result1 = sign_content(content, agent_id, private_key, timestamp)
    result2 = sign_content(content, agent_id, private_key, timestamp)
    
    # Results should be identical
    assert result1 == result2


def test_sign_content_different_content_different_signature(test_keypair):
    """Test that different content produces different signatures."""
    private_key, _ = test_keypair
    
    agent_id = "test-agent"
    timestamp = 1640995200.0
    
    result1 = sign_content("content1", agent_id, private_key, timestamp)
    result2 = sign_content("content2", agent_id, private_key, timestamp)
    
    # Signatures should be different
    assert result1["signature"] != result2["signature"]
    assert result1["content_hash"] != result2["content_hash"]


def test_sign_content_timestamp_default():
    """Test that timestamp defaults to current time."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    import time
    before = time.time()
    result = sign_content("test", "agent", private_pem)
    after = time.time()
    
    assert before <= result["timestamp"] <= after


def test_sign_content_invalid_agent_id(test_keypair):
    """Test validation of agent_id format."""
    private_key, _ = test_keypair
    
    # Test invalid characters
    with pytest.raises(ValueError, match="agent_id must match pattern"):
        sign_content("test", "invalid@agent", private_key)
    
    # Test empty string
    with pytest.raises(ValueError, match="agent_id must match pattern"):
        sign_content("test", "", private_key)
    
    # Test too long
    with pytest.raises(ValueError, match="agent_id must match pattern"):
        sign_content("test", "a" * 65, private_key)


def test_sign_content_invalid_private_key():
    """Test handling of invalid private key."""
    with pytest.raises(ValueError, match="Invalid private key format"):
        sign_content("test", "agent", "not-a-key")
    
    with pytest.raises(ValueError, match="Invalid private key format"):
        sign_content("test", "agent", "-----BEGIN INVALID-----\ndata\n-----END INVALID-----")


def test_sign_content_non_string_content(test_keypair):
    """Test type validation for content parameter."""
    private_key, _ = test_keypair
    
    with pytest.raises(TypeError, match="content must be a string"):
        sign_content(123, "agent", private_key)
    
    with pytest.raises(TypeError, match="content must be a string"):
        sign_content(["list"], "agent", private_key)
    
    with pytest.raises(TypeError, match="content must be a string"):
        sign_content(None, "agent", private_key)


def test_sign_content_valid_agent_id_formats(test_keypair):
    """Test various valid agent_id formats."""
    private_key, _ = test_keypair
    
    valid_ids = [
        "agent",
        "agent-1",
        "agent_2", 
        "Agent123",
        "a" * 64,  # Max length
        "123",
        "a-b_c"
    ]
    
    for agent_id in valid_ids:
        result = sign_content("test", agent_id, private_key, 1640995200.0)
        assert result["agent_id"] == agent_id


def test_sign_content_json_serializable(test_keypair):
    """Test that the result can be serialized to JSON."""
    private_key, _ = test_keypair
    
    result = sign_content("test content", "agent", private_key, 1640995200.0)
    
    # Should be able to serialize to JSON and back
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    
    assert parsed == result
