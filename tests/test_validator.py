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
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is True
        assert errors == []
    
    def test_valid_manifest_with_iso_format_variations(self):
        """Test validation with different valid ISO 8601 timestamp formats."""
        timestamps = [
            '2024-01-15T10:30:00Z',
            '2024-01-15T10:30:00+00:00',
            '2024-01-15T10:30:00.123Z',
            '2024-01-15T10:30:00.123456+00:00',
            '2024-01-15T10:30:00'
        ]
        
        base_manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'signature': 'base64encodedSignature=='
        }
        
        for timestamp in timestamps:
            manifest = {**base_manifest, 'timestamp': timestamp}
            is_valid, errors = validate_manifest(manifest)
            assert is_valid is True, f"Failed for timestamp: {timestamp}, errors: {errors}"
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
            'model': 'gpt-4',
            'output_hash': None,
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' cannot be null" in errors
        assert "Field 'output_hash' cannot be null" in errors
    
    def test_empty_fields(self):
        """Test validation fails when required fields are empty strings."""
        manifest = {
            'version': '',
            'provider': '   ',  # whitespace only
            'model': 'gpt-4',
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' cannot be empty" in errors
        assert "Field 'provider' cannot be empty" in errors
    
    def test_non_string_fields(self):
        """Test validation fails when fields are not strings."""
        manifest = {
            'version': 1.0,  # number instead of string
            'provider': 'openai',
            'model': ['gpt-4'],  # list instead of string
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'version' must be a string" in errors
        assert "Field 'model' must be a string" in errors
    
    def test_invalid_output_hash_format(self):
        """Test validation fails when output_hash doesn't start with 'sha256:'."""
        manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'md5:invalidhash',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert "Field 'output_hash' must start with 'sha256:'" in errors
    
    def test_invalid_output_hash_hex(self):
        """Test validation fails when output_hash has invalid hex characters."""
        test_cases = [
            'sha256:invalidhex',  # not hex
            'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567',  # too short
            'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890a',  # too long
            'sha256:g1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',  # invalid hex char 'g'
        ]
        
        base_manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'timestamp': '2024-01-15T10:30:00Z',
            'signature': 'base64encodedSignature=='
        }
        
        for invalid_hash in test_cases:
            manifest = {**base_manifest, 'output_hash': invalid_hash}
            is_valid, errors = validate_manifest(manifest)
            assert is_valid is False, f"Should fail for hash: {invalid_hash}"
            assert "Field 'output_hash' must contain a valid 64-character hex hash after 'sha256:'" in errors
    
    def test_invalid_timestamp_format(self):
        """Test validation fails when timestamp is not valid ISO 8601."""
        invalid_timestamps = [
            '2024-01-15 10:30:00',  # space instead of T
            '2024/01/15T10:30:00Z',  # slashes instead of dashes
            '15-01-2024T10:30:00Z',  # wrong date order
            '2024-13-15T10:30:00Z',  # invalid month
            '2024-01-32T10:30:00Z',  # invalid day
            '2024-01-15T25:30:00Z',  # invalid hour
            'not-a-date',
            ''
        ]
        
        base_manifest = {
            'version': '1.0.0',
            'provider': 'openai',
            'model': 'gpt-4',
            'output_hash': 'sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890',
            'challenge_token': 'agentmark-f475ae398d88e4cd',
            'pipeline_key': 'test-pipeline-123',
            'signature': 'base64encodedSignature=='
        }
        
        for invalid_timestamp in invalid_timestamps:
            manifest = {**base_manifest, 'timestamp': invalid_timestamp}
            is_valid, errors = validate_manifest(manifest)
            assert is_valid is False, f"Should fail for timestamp: {invalid_timestamp}"
            if invalid_timestamp:  # empty string will fail on empty field check first
                assert "Field 'timestamp' must be in valid ISO 8601 format" in errors
    
    def test_empty_manifest(self):
        """Test validation fails for completely empty manifest."""
        manifest = {}
        
        is_valid, errors = validate_manifest(manifest)
        assert is_valid is False
        assert len(errors) == 8  # All 8 required fields missing
        
        required_fields = [
            'version', 'provider', 'model', 'output_hash',
            'challenge_token', 'pipeline_key', 'timestamp', 'signature'
        ]
        
        for field in required_fields:
            assert f"Missing required field: {field}" in errors
