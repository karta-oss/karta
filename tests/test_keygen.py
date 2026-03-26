"""Tests for agentmark key generation functionality."""

import os
import tempfile
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from agentmark.keygen import generate_keypair, save_keypair


class TestGenerateKeypair:
    """Test key pair generation."""
    
    def test_generate_valid_keypair(self):
        """Test generating a valid RSA-2048 key pair."""
        agent_id = "test_agent_123"
        private_pem, public_pem = generate_keypair(agent_id)
        
        # Verify both keys are PEM format strings
        assert isinstance(private_pem, str)
        assert isinstance(public_pem, str)
        assert private_pem.startswith("-----BEGIN RSA PRIVATE KEY-----")
        assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
        
        # Verify keys can be loaded
        private_key = serialization.load_pem_private_key(
            private_pem.encode(), password=None
        )
        public_key = serialization.load_pem_public_key(public_pem.encode())
        
        # Verify key size is 2048 bits
        assert private_key.key_size == 2048
        assert public_key.key_size == 2048
    
    def test_invalid_agent_id_format(self):
        """Test error on invalid agent_id format."""
        with pytest.raises(ValueError, match="must match"):
            generate_keypair("invalid id with spaces")
        
        with pytest.raises(ValueError, match="must match"):
            generate_keypair("invalid@id")
        
        with pytest.raises(ValueError, match="must match"):
            generate_keypair("")
        
        with pytest.raises(ValueError, match="must match"):
            generate_keypair("a" * 65)  # Too long
    
    def test_non_string_agent_id(self):
        """Test error on non-string agent_id."""
        with pytest.raises(ValueError, match="must be a string"):
            generate_keypair(123)
        
        with pytest.raises(ValueError, match="must be a string"):
            generate_keypair(None)


class TestSaveKeypair:
    """Test key pair saving functionality."""
    
    def test_save_keypair_success(self):
        """Test successful key pair saving."""
        agent_id = "test_save"
        private_pem, public_pem = generate_keypair(agent_id)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            private_path, public_path = save_keypair(
                agent_id, private_pem, public_pem, temp_dir
            )
            
            # Verify files were created
            assert os.path.exists(private_path)
            assert os.path.exists(public_path)
            
            # Verify file names
            assert private_path.endswith(f"{agent_id}.private.pem")
            assert public_path.endswith(f"{agent_id}.public.pem")
            
            # Verify file contents
            with open(private_path) as f:
                assert f.read() == private_pem
            
            with open(public_path) as f:
                assert f.read() == public_pem
    
    def test_save_keypair_file_exists(self):
        """Test error when files already exist."""
        agent_id = "test_exists"
        private_pem, public_pem = generate_keypair(agent_id)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files first time
            save_keypair(agent_id, private_pem, public_pem, temp_dir)
            
            # Try to create again without force
            with pytest.raises(FileExistsError, match="already exist"):
                save_keypair(agent_id, private_pem, public_pem, temp_dir)
    
    def test_save_keypair_force_overwrite(self):
        """Test overwriting existing files with force=True."""
        agent_id = "test_force"
        private_pem, public_pem = generate_keypair(agent_id)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files first time
            save_keypair(agent_id, private_pem, public_pem, temp_dir)
            
            # Overwrite with force=True
            private_path, public_path = save_keypair(
                agent_id, private_pem, public_pem, temp_dir, force=True
            )
            
            # Verify files still exist
            assert os.path.exists(private_path)
            assert os.path.exists(public_path)