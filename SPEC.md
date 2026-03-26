# SPEC.md
# Agent Protocol Specification

## Problem Statement and Vision

Autonomous agents need a standardized protocol for secure, typed communication. Currently, multi-agent systems use ad-hoc message formats, leading to incompatible implementations and fragile coordination patterns. This project defines a comprehensive protocol specification with validation framework that enables reliable agent-to-agent communication.

The vision: Any agent can communicate with any other agent using standardized message formats, handshake procedures, and validation rules. This creates an interoperable ecosystem where agents from different frameworks can collaborate seamlessly.

## Agent User Stories

**Agent Framework Developers** use this library to implement standardized communication in their frameworks, ensuring compatibility with other agent systems.

**Multi-Agent System Builders** use this protocol to enable coordination between heterogeneous agents without custom message translation layers.

**Agent Instance Developers** use the validation framework to ensure their agents send and receive correctly formatted messages.

**Protocol Researchers** use this as a foundation for studying agent communication patterns and developing new coordination mechanisms.

## Public API Contract

### Core Classes

```python
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import jsonschema

class MessageType(Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE" 
    NOTIFICATION = "NOTIFICATION"
    ERROR = "ERROR"
    HELLO = "HELLO"
    CAPABILITY = "CAPABILITY"
    ACK = "ACK"

class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid: bool = is_valid
        self.errors: List[str] = errors

class AgentMessage:
    def __init__(self, 
                 message_id: str,
                 message_type: MessageType,
                 sender_id: str,
                 payload: Dict[str, Any],
                 timestamp: Optional[str] = None,
                 correlation_id: Optional[str] = None,
                 target_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.message_id: str = message_id
        self.message_type: MessageType = message_type
        self.sender_id: str = sender_id
        self.payload: Dict[str, Any] = payload
        self.timestamp: Optional[str] = timestamp
        self.correlation_id: Optional[str] = correlation_id
        self.target_id: Optional[str] = target_id
        self.metadata: Optional[Dict[str, Any]] = metadata
    
    def to_dict(self) -> Dict[str, Any]: ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage': ...

class MessageValidator:
    def __init__(self, schema_registry: 'SchemaRegistry'):
        self._schema_registry: SchemaRegistry = schema_registry
    
    def validate(self, message: Union[Dict[str, Any], AgentMessage]) -> ValidationResult: ...
    
    def validate_batch(self, messages: List[Union[Dict[str, Any], AgentMessage]]) -> List[ValidationResult]: ...

class MessageTypeRegistry:
    def __init__(self):
        self._schemas: Dict[MessageType, Dict[str, Any]] = {}
        self._custom_schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_builtin_type(self, message_type: MessageType, schema: Dict[str, Any]) -> None: ...
    
    def register_custom_type(self, type_name: str, schema: Dict[str, Any]) -> None: ...
    
    def get_schema(self, message_type: Union[MessageType, str]) -> Dict[str, Any]: ...
    
    def list_types(self) -> List[Union[MessageType, str]]: ...

class HandshakeValidator:
    def __init__(self, schema_registry: 'SchemaRegistry'):
        self._schema_registry: SchemaRegistry = schema_registry
        self._state_machine: Dict[str, List[MessageType]] = {}
    
    def validate_handshake_sequence(self, messages: List[AgentMessage], session_id: str) -> ValidationResult: ...
    
    def get_next_expected_types(self, session_id: str) -> List[MessageType]: ...
    
    def reset_session(self, session_id: str) -> None: ...

class SchemaRegistry:
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None: ...
    
    def get_schema(self, name: str) -> Dict[str, Any]: ...
    
    def validate_against_schema(self, data: Dict[str, Any], schema_name: str) -> ValidationResult: ...
```

### Protocol Specification Generator

```python
class ProtocolDocumentationGenerator:
    def __init__(self, schema_registry: SchemaRegistry, type_registry: MessageTypeRegistry):
        self._schema_registry: SchemaRegistry = schema_registry
        self._type_registry: MessageTypeRegistry = type_registry
    
    def generate_markdown_spec(self) -> str: ...
    
    def generate_message_examples(self) -> Dict[str, Dict[str, Any]]: ...
    
    def generate_handshake_flow_diagram(self) -> str: ...
    
    def generate_version_compatibility_matrix(self) -> str: ...
```

## Data Schemas

### Core Message Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentMessage",
  "type": "object",
  "required": ["message_id", "message_type", "sender_id", "payload"],
  "properties": {
    "message_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]+$",
      "minLength": 1,
      "maxLength": 128
    },
    "message_type": {
      "type": "string",
      "enum": ["REQUEST", "RESPONSE", "NOTIFICATION", "ERROR", "HELLO", "CAPABILITY", "ACK"]
    },
    "sender_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_.-]+$",
      "minLength": 1,
      "maxLength": 64
    },
    "payload": {
      "type": "object"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "correlation_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]+$",
      "maxLength": 128
    },
    "target_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_.-]+$",
      "maxLength": 64
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

### Handshake Message Schemas

```json
{
  "HELLO": {
    "type": "object",
    "required": ["protocol_version", "agent_capabilities"],
    "properties": {
      "protocol_version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
      "agent_capabilities": {
        "type": "array",
        "items": {"type": "string"}
      },
      "session_timeout": {"type": "integer", "minimum": 0},
      "supported_transports": {
        "type": "array", 
        "items": {"type": "string"}
      }
    }
  },
  "CAPABILITY": {
    "type": "object",
    "required": ["offered_capabilities", "required_capabilities"],
    "properties": {
      "offered_capabilities": {
        "type": "array",
        "items": {"type": "string"}
      },
      "required_capabilities": {
        "type": "array",
        "items": {"type": "string"}
      },
      "negotiation_preferences": {"type": "object"}
    }
  },
  "ACK": {
    "type": "object",
    "required": ["status"],
    "properties": {
      "status": {"type": "string", "enum": ["accepted", "rejected", "partial"]},
      "agreed_capabilities": {
        "type": "array",
        "items": {"type": "string"}
      },
      "session_id": {"type": "string"},
      "rejection_reason": {"type": "string"}
    }
  }
}
```

### Built-in Message Type Schemas

```json
{
  "REQUEST": {
    "type": "object",
    "required": ["action", "parameters"],
    "properties": {
      "action": {"type": "string"},
      "parameters": {"type": "object"},
      "timeout": {"type": "integer", "minimum": 0},
      "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]}
    }
  },
  "RESPONSE": {
    "type": "object",
    "required": ["status"],
    "properties": {
      "status": {"type": "string", "enum": ["success", "error", "partial"]},
      "result": {"type": "object"},
      "error": {
        "type": "object",
        "properties": {
          "code": {"type": "string"},
          "message": {"type": "string"},
          "details": {"type": "object"}
        }
      }
    }
  },
  "NOTIFICATION": {
    "type": "object",
    "required": ["event_type"],
    "properties": {
      "event_type": {"type": "string"},
      "data": {"type": "object"},
      "severity": {"type": "string", "enum": ["info", "warning", "error"]}
    }
  },
  "ERROR": {
    "type": "object",
    "required": ["error_code", "error_message"],
    "properties": {
      "error_code": {"type": "string"},
      "error_message": {"type": "string"},
      "error_details": {"type": "object"},
      "recovery_suggestions": {
        "type": "array",
        "items": {"type": "string"}
      }
    }
  }
}
```

## Error Handling Contract

### Validation Errors

All validation methods return `ValidationResult` objects, never raise exceptions for invalid data. Validation errors include:

- **Schema Validation Errors**: Field missing, wrong type, constraint violation
- **Format Errors**: Invalid message_id pattern, malformed timestamp
- **Protocol Errors**: Invalid handshake sequence, unknown message type
- **Logic Errors**: Missing correlation_id for RESPONSE, target_id for REQUEST

Error messages must be machine-parseable with format:
```
"field_name: error_description (expected: expected_value, got: actual_value)"
```

### System Errors

Library code may raise these exceptions:

- `SchemaNotFoundError`: When requesting unregistered schema
- `InvalidSchemaError`: When registering malformed JSON schema  
- `ProtocolVersionError`: When protocol versions are incompatible
- `HandshakeTimeoutError`: When handshake doesn't complete in time

### Error Message Schema

```json
{
  "type": "object",
  "required": ["error_code", "error_message", "timestamp"],
  "properties": {
    "error_code": {
      "type": "string",
      "enum": [
        "VALIDATION_FAILED",
        "SCHEMA_NOT_FOUND", 
        "PROTOCOL_VERSION_MISMATCH",
        "HANDSHAKE_FAILED",
        "TIMEOUT",
        "CAPABILITY_MISMATCH"
      ]
    },
    "error_message": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "context": {"type": "object"},
    "recovery_actions": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

## Performance Constraints

- Message validation must complete in <10ms for messages up to 1MB
- Schema compilation must complete in <100ms for schemas up to 10KB
- Memory usage must not exceed 2x message size during validation
- Batch validation must process 1000 messages/second on standard hardware
- Handshake validation state machine must support 10,000 concurrent sessions
- Schema registry must support 1000 registered schemas without degradation

## Extension Points

### 1. Custom Message Types

**How to add**: Register new message types with the `MessageTypeRegistry`

```python
# Agent contributor adds custom auction message type
auction_schema = {
    "type": "object",
    "required": ["auction_id", "bid_amount", "item_description"],
    "properties": {
        "auction_id": {"type": "string"},
        "bid_amount": {"type": "number", "minimum": 0},
        "item_description": {"type": "string"},
        "max_bid": {"type": "number"},
        "deadline": {"type": "string", "format": "date-time"}
    }
}

registry = MessageTypeRegistry()
registry.register_custom_type("AUCTION_BID", auction_schema)
```

**Integration point**: Custom types automatically work with existing validation framework.

### 2. Transport Adapters

**How to add**: Implement `TransportAdapter` interface (added in v2.0)

```python
# Future extension point - v2.0
class TransportAdapter(ABC):
    @abstractmethod
    def send_message(self, message: AgentMessage, destination: str) -> bool: ...
    
    @abstractmethod
    def receive_message(self) -> Optional[AgentMessage]: ...
    
    @abstractmethod
    def supports_transport(self, transport_type: str) -> bool: ...

# Agent contributor adds WebSocket adapter
class WebSocketAdapter(TransportAdapter):
    def send_message(self, message: AgentMessage, destination: str) -> bool:
        # WebSocket-specific implementation
        pass
```

**Registration**: `TransportRegistry.register_adapter("websocket", WebSocketAdapter())`

### 3. Protocol Extensions

**How to add**: Create protocol extension modules that add new handshake patterns

```python
# Future extension point - v3.0+
class ConsensusProtocolExtension:
    def get_additional_message_types(self) -> Dict[str, Dict[str, Any]]:
        return {
            "CONSENSUS_PROPOSE": {...},
            "CONSENSUS_VOTE": {...},
            "CONSENSUS_COMMIT": {...}
        }
    
    def get_handshake_extensions(self) -> Dict[str, Any]:
        return {"consensus_algorithm": "raft"}
```

**Registration**: `ProtocolExtensionRegistry.register("consensus", ConsensusProtocolExtension())`

### 4. Validation Plugins

**How to add**: Implement `ValidationPlugin` interface for custom validation logic

```python
# Future extension point - v2.0+
class ValidationPlugin(ABC):
    @abstractmethod
    def validate(self, message: AgentMessage, context: Dict[str, Any]) -> ValidationResult: ...
    
    @abstractmethod
    def get_plugin_name(self) -> str: ...

# Agent contributor adds semantic validation
class SemanticValidationPlugin(ValidationPlugin):
    def validate(self, message: AgentMessage, context: Dict[str, Any]) -> ValidationResult:
        # Check message semantics, not just structure
        pass
```

**Integration**: Plugins run after schema validation as additional validation layer.

### 5. Schema Generators

**How to add**: Create schema generators for domain-specific message patterns

```python
# Future extension point - v3.0+
class SchemaGenerator(ABC):
    @abstractmethod
    def generate_schema(self, pattern_config: Dict[str, Any]) -> Dict[str, Any]: ...

# Agent contributor adds workflow schema generator
class WorkflowSchemaGenerator(SchemaGenerator):
    def generate_schema(self, pattern_config: Dict[str, Any]) -> Dict[str, Any]:
        # Generate schemas for workflow coordination patterns
        pass
```

**Usage**: `schema = WorkflowSchemaGenerator().generate_schema({"pattern": "dag_execution"})`

### 6. Documentation Extensions

**How to add**: Implement `DocumentationExtension` for custom spec generation

```python
# Future extension point - v2.0+
class DocumentationExtension(ABC):
    @abstractmethod
    def generate_section(self, context: Dict[str, Any]) -> str: ...
    
    @abstractmethod
    def get_section_name(self) -> str: ...

# Agent contributor adds security documentation section
class SecurityDocExtension(DocumentationExtension):
    def generate_section(self, context: Dict[str, Any]) -> str:
        return "## Security Considerations\n..."
```

**Integration**: Extensions automatically included in generated protocol documentation.

### 7. Language Bindings

**How to add**: Use schema definitions to generate bindings for other languages

```bash
# Future tooling - v5.0+
agent-protocol generate --language rust --output ./rust-bindings/
agent-protocol generate --language javascript --output ./js-bindings/
```

**Template system**: JSON schema + language templates = generated bindings

## v1.0 Scope

### Included Features

1. **Core Message Schema**: Complete JSON schema for `AgentMessage` with all required and optional fields
2. **Message Validation Framework**: `MessageValidator` class with comprehensive validation logic
3. **Message Type Registry**: Built-in types (REQUEST, RESPONSE, NOTIFICATION, ERROR) plus custom type registration
4. **Handshake Protocol**: HELLO/CAPABILITY/ACK sequence with validation state machine
5. **Schema Registry**: Central registry for all protocol schemas with validation
6. **Documentation Generator**: Automatic spec generation from schemas and code
7. **Python API**: Complete Python library with type hints and comprehensive error handling
8. **Test Suite**: 100% test coverage with message examples and validation scenarios

### Implementation Files

- `agent_protocol/schemas/` - All JSON schema definitions
- `agent_protocol/validation.py` - MessageValidator and ValidationResult classes  
- `agent_protocol/registry.py` - MessageTypeRegistry and SchemaRegistry classes
- `agent_protocol/handshake.py` - HandshakeValidator and handshake logic
- `agent_protocol/messages.py` - AgentMessage class and MessageType enum
- `agent_protocol/documentation.py` - ProtocolDocumentationGenerator class
- `agent_protocol/errors.py` - All custom exception classes
- `tests/` - Comprehensive test suite with 100% coverage

## Explicit Non-Goals (v1.0)

1. **Transport Implementations**: No WebSocket, gRPC, or HTTP adapters
2. **Security Mechanisms**: No message signing, encryption, or authentication
3. **Discovery Services**: No agent discovery or registry services
4. **Performance Monitoring**: No metrics collection or performance analysis
5. **Language Bindings**: Only Python, no JavaScript/Rust/Go bindings
6. **Advanced Patterns**: No consensus, auction, or delegation protocols
7. **Persistence**: No message queuing, storage, or replay capabilities
8. **Network Layer**: No connection management or retry logic

## Acceptance Criteria

### Core Functionality

- [ ] AgentMessage class serializes/deserializes correctly to/from JSON
- [ ] MessageValidator validates all built-in message types correctly  
- [ ] MessageValidator rejects invalid messages with clear error descriptions
- [ ] HandshakeValidator enforces correct HELLO → CAPABILITY → ACK sequence
- [ ] MessageTypeRegistry supports custom message type registration
- [ ] SchemaRegistry validates schemas against JSON Schema Draft 7
- [ ] Documentation generator produces complete markdown specification

### Quality Gates

- [ ] 100% test coverage across all modules
- [ ] All public APIs have comprehensive docstrings with examples
- [ ] Type hints on all function signatures and class attributes
- [ ] Zero linting errors with flake8 and mypy
- [ ] All validation errors include field-level detail and recovery suggestions
- [ ] Performance tests validate sub-10ms validation for 1MB messages

### Integration Tests

- [ ] Round-trip message serialization preserves all data
- [ ] Batch validation processes 1000+ messages without memory growth
- [ ] Handshake validation handles 1000+ concurrent sessions
- [ ] Custom message types integrate seamlessly with validation framework
- [ ] Generated documentation matches manual examples exactly

## Security Constraints

### v1.0 Security Requirements

1. **Input Validation**: All message inputs must be validated against schemas before processing
2. **Schema Safety**: Registered schemas must not allow arbitrary code execution
3. **Memory Bounds**: Message size limits prevent DoS via large payloads (max 10MB per message)
4. **No Deserialization Attacks**: JSON parsing only, no pickle or other executable formats
5. **Error Information Leakage**: Validation errors must not expose internal system details

### Security Non-Goals (v1.0)

- Message authentication/signing (planned for v4.0)
- Message encryption (planned for v4.0)  
- Transport security (TLS/etc - handled by transport layer)
- Rate limiting (handled by transport/application layer)
- Agent identity verification (planned for v2.0)

### Security Extension Points

Future agents can add security extensions via:

```python
# v4.0+ extension point
class SecurityExtension(ABC):
    @abstractmethod
    def sign_message(self, message: AgentMessage, key: Any) -> str: ...
    
    @abstractmethod
    def verify_signature(self, message: AgentMessage, signature: str, key: Any) -> bool: ...
```

## Approved Dependencies

### Required Dependencies

- `jsonschema>=4.0.0,<5.0.0` - JSON schema validation
- `typing-extensions>=4.0.0` - Enhanced type hints for Python <3.10

### Standard Library Only

- `json` - Message serialization/deserialization
- `datetime` - Timestamp handling
- `enum` - MessageType enumeration
- `abc` - Abstract base classes for extension points
- `typing` - Type hints and generics
- `uuid` - Message ID generation utilities
- `re` - Pattern validation for IDs

### Forbidden Dependencies

- No web frameworks (Flask, FastAPI, etc.)
- No async frameworks (asyncio extensions, trio, etc.)
- No transport libraries (websockets, grpcio, etc.)
- No external validation libraries beyond jsonschema
- No logging frameworks (use standard library logging only)

## Test Requirements

### Unit Test Coverage

- **100% line coverage** across all modules
- **100% branch coverage** for all conditional logic
- **Property-based testing** for message validation using hypothesis
- **Schema validation testing** against both valid and invalid examples
- **Error path testing** for all validation and parsing edge cases

### Test Categories

1. **Schema Tests**: Every JSON schema validates correct examples and rejects incorrect ones
2. **Validation Tests**: MessageValidator handles all message types and error conditions
3. **Handshake Tests**: All valid handshake sequences pass, invalid sequences fail
4. **Registry Tests**: Type and schema registration/lookup with error handling
5. **Serialization Tests**: Round-trip JSON serialization preserves all data
6. **Performance Tests**: Validation speed benchmarks for various message sizes
7. **Integration Tests**: End-to-end scenarios combining multiple components

### Test Data Requirements

- **Valid message examples** for each built-in message type
- **Invalid message examples** covering every validation rule
- **Handshake sequence examples** for successful and failed negotiations  
- **Custom message type examples** demonstrating extensibility
- **Edge case examples** (empty payloads, max-size messages, Unicode handling)

### Continuous Integration

- Tests run on Python 3.8, 3.9, 3.10, 3.11
- Tests run on Linux, macOS, Windows
- Performance regression detection on validation speed
- Memory usage monitoring during batch validation
- Documentation generation validation (generated docs must build successfully)