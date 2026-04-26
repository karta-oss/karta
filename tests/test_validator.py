"""Tests for agentmark manifest validator."""

import pytest
from src.validator import validate_manifest


class TestValidateManifest:
    """Test cases for validate_manifest function."""
    
    def test_valid_manifest(self):
        """Test validation of a valid manifest."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'agentmark-a4e6a0ba0602067e',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is True
        assert errors == []
    
    def test_valid_manifest_with_iso_offset(self):
        """Test validation with ISO 8601 timestamp with timezone offset."""
        manifest = {
            'version': '1.0.0',
            'provider': 'anthropic',
            'model': 'claude-3',
            'output_hash': 'sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
            'challenge_token': 'token-123',
            'pipeline_key': 'pipeline-456',
            'timestamp': '2024-01-15T10:30:00+05:00',
            'signature': 'signature123'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is True
        assert errors == []
    
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai'
            # Missing other required fields
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert len(errors) == 6  # 6 missing fields
        assert 'Missing required field: model' in errors
        assert 'Missing required field: output_hash' in errors
        assert 'Missing required field: challenge_token' in errors
        assert 'Missing required field: pipeline_key' in errors
        assert 'Missing required field: timestamp' in errors
        assert 'Missing required field: signature' in errors
    
    def test_null_fields(self):
        """Test validation fails when required fields are null."""
        manifest = {
            'version': None,
            'provider': 'openai',
            'model': None,
            'output_hash': 'sha256:abc123',
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' cannot be null" in errors
        assert "Field 'model' cannot be null" in errors
    
    def test_non_string_fields(self):
        """Test validation fails when fields are not strings."""
        manifest = {
            'version': 1.0,  # Should be string
            'provider': 'openai',
            'model': ['gpt-4'],  # Should be string
            'output_hash': 'sha256:abc123',
            'challenge_token': 123,  # Should be string
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' must be a string" in errors
        assert "Field 'model' must be a string" in errors
        assert "Field 'challenge_token' must be a string" in errors
    
    def test_empty_fields(self):
        """Test validation fails when fields are empty strings."""
        manifest = {
            'version': '',
            'provider': '   ',  # Whitespace only
            'model': 'gpt-4',
            'output_hash': 'sha256:abc123',
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' cannot be empty" in errors
        assert "Field 'provider' cannot be empty" in errors
    
    def test_invalid_output_hash_format(self):
        """Test validation fails when output_hash doesn't start with 'sha256:'."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'md5:abc123',  # Wrong prefix
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "output_hash must start with 'sha256:'" in errors
    
    def test_invalid_output_hash_hex(self):
        """Test validation fails when output_hash has invalid hex characters."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:xyz123',  # Invalid hex
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "output_hash must contain a valid 64-character hex SHA-256 hash after 'sha256:'" in errors
    
    def test_invalid_output_hash_length(self):
        """Test validation fails when output_hash has wrong length."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:abc123',  # Too short
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "output_hash must contain a valid 64-character hex SHA-256 hash after 'sha256:'" in errors
    
    def test_invalid_timestamp_format(self):
        """Test validation fails when timestamp is not valid ISO 8601."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': '2024/01/15 10:30:00',  # Wrong format
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "timestamp must be in valid ISO 8601 format" in errors
    
    def test_multiple_errors(self):
        """Test validation returns multiple errors when multiple issues exist."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'md5:abc123',  # Wrong format
            'challenge_token': 'token',
            'pipeline_key': 'key',
            'timestamp': 'invalid-date',  # Invalid timestamp
            'signature': 'sig'
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert len(errors) == 2
        assert "output_hash must start with 'sha256:'" in errors
        assert "timestamp must be in valid ISO 8601 format" in errors
    
    def test_empty_manifest(self):
        """Test validation fails for completely empty manifest."""
        manifest = {}
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert len(errors) == 8  # All required fields missing
