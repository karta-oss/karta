"""Agentmark manifest validator utility."""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any


def validate_manifest(manifest: dict) -> Tuple[bool, List[str]]:
    """
    Validate an agentmark manifest JSON object.
    
    Args:
        manifest: Dictionary containing manifest data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        - (True, []) if valid
        - (False, [list of errors]) if invalid
    """
    errors = []
    
    # Required fields
    required_fields = [
        'version',
        'provider', 
        'model',
        'output_hash',
        'challenge_token',
        'pipeline_key',
        'timestamp',
        'signature'
    ]
    
    # Check for missing required fields
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
        elif manifest[field] is None:
            errors.append(f"Field '{field}' cannot be null")
        elif not isinstance(manifest[field], str):
            errors.append(f"Field '{field}' must be a string")
        elif not manifest[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
    
    # If basic validation failed, return early
    if errors:
        return False, errors
    
    # Validate output_hash format
    output_hash = manifest.get('output_hash', '')
    if not output_hash.startswith('sha256:'):
        errors.append("output_hash must start with 'sha256:'")
    else:
        # Check if the hash part after 'sha256:' is valid hex
        hash_part = output_hash[7:]  # Remove 'sha256:' prefix
        if not re.match(r'^[a-fA-F0-9]{64}$', hash_part):
            errors.append("output_hash must contain a valid 64-character hex SHA-256 hash after 'sha256:'")
    
    # Validate timestamp is valid ISO 8601 format
    timestamp = manifest.get('timestamp', '')
    try:
        # Try to parse as ISO 8601
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        errors.append("timestamp must be in valid ISO 8601 format")
    
    return len(errors) == 0, errors
