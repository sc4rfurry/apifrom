"""
Serialization utilities for APIFromAnything.

This module provides utilities for serializing and deserializing data.
"""

import datetime
import decimal
import enum
import inspect
import json
import logging
import typing as t
import uuid
from dataclasses import asdict, is_dataclass

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for APIFromAnything.
    
    This encoder handles common Python types that are not natively supported by JSON.
    """
    
    def default(self, obj):
        """
        Convert an object to a JSON-serializable type.
        
        Args:
            obj: The object to convert.
            
        Returns:
            A JSON-serializable representation of the object.
        """
        # Handle datetime objects
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        
        # Handle UUID objects
        if isinstance(obj, uuid.UUID):
            return str(obj)
        
        # Handle Decimal objects
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        
        # Handle Enum objects
        if isinstance(obj, enum.Enum):
            return obj.value
        
        # Handle dataclasses
        if is_dataclass(obj):
            return asdict(obj)
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        
        # Handle objects with a to_dict method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        
        # Handle objects with a __dict__ attribute
        if hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        
        # Let the parent class handle it or raise TypeError
        return super().default(obj)


def serialize(obj: t.Any) -> t.Any:
    """
    Serialize an object to a JSON-compatible type.
    
    Args:
        obj: The object to serialize.
        
    Returns:
        A JSON-compatible representation of the object.
    """
    if obj is None:
        return None
    
    try:
        # Use dumps/loads to leverage the custom encoder
        return json.loads(json.dumps(obj, cls=JSONEncoder))
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize object: {e}")
        return str(obj)


def deserialize(data: t.Any, target_type: t.Union[t.Type, t.Any]) -> t.Any:
    """
    Deserialize data to a specific type.
    
    Args:
        data: The data to deserialize.
        target_type: The target type.
        
    Returns:
        The deserialized data.
    """
    if data is None:
        return None
    
    # Handle Any type
    if target_type is t.Any:
        return data
    
    # Handle Union types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is t.Union:
        # Try each type in the union
        for arg in target_type.__args__:
            try:
                return deserialize(data, arg)
            except ValueError:
                continue
        
        # If we get here, none of the types worked
        raise ValueError(f"Could not deserialize {data} to any of {target_type.__args__}")
    
    # Handle Optional types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is t.Union and type(None) in target_type.__args__:
        if data is None:
            return None
        
        # Get the non-None type
        non_none_type = next(arg for arg in target_type.__args__ if arg is not type(None))
        return deserialize(data, non_none_type)
    
    # Handle List types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is list:
        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data)}")
        
        # Get the item type
        item_type = target_type.__args__[0]
        return [deserialize(item, item_type) for item in data]
    
    # Handle Tuple types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is tuple:
        if not isinstance(data, (list, tuple)):
            raise ValueError(f"Expected list or tuple, got {type(data)}")
        
        # Convert to tuple
        if len(target_type.__args__) == 2 and target_type.__args__[1] is Ellipsis:
            # Handle Tuple[T, ...] - variable length tuple
            item_type = target_type.__args__[0]
            return tuple(deserialize(item, item_type) for item in data)
        else:
            # Handle Tuple[T1, T2, ...] - fixed length tuple
            if len(data) != len(target_type.__args__):
                raise ValueError(f"Expected tuple of length {len(target_type.__args__)}, got {len(data)}")
            
            return tuple(deserialize(item, arg_type) for item, arg_type in zip(data, target_type.__args__))
    
    # Handle Set types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is set:
        if not isinstance(data, (list, set, tuple)):
            raise ValueError(f"Expected list, set, or tuple, got {type(data)}")
        
        # Get the item type
        item_type = target_type.__args__[0]
        return {deserialize(item, item_type) for item in data}
    
    # Handle Dict types
    if hasattr(target_type, "__origin__") and target_type.__origin__ is dict:
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")
        
        # Get the key and value types
        key_type, value_type = target_type.__args__
        return {deserialize(k, key_type): deserialize(v, value_type) for k, v in data.items()}
    
    # Handle Enum types
    try:
        if inspect.isclass(target_type) and issubclass(target_type, enum.Enum):
            # Try to convert the value to an enum
            return target_type(data)
    except (TypeError, ValueError):
        pass
    
    # Handle basic types
    if target_type is str:
        return str(data)
    elif target_type is int:
        return int(data)
    elif target_type is float:
        return float(data)
    elif target_type is bool:
        return bool(data)
    elif target_type is list:
        return list(data)
    elif target_type is dict:
        return dict(data)
    
    # Handle datetime types
    if target_type is datetime.datetime:
        if isinstance(data, str):
            return datetime.datetime.fromisoformat(data)
        elif isinstance(data, (int, float)):
            return datetime.datetime.fromtimestamp(data)
        else:
            raise ValueError(f"Cannot convert {data} to datetime")
    
    if target_type is datetime.date:
        if isinstance(data, str):
            return datetime.date.fromisoformat(data)
        else:
            raise ValueError(f"Cannot convert {data} to date")
    
    if target_type is datetime.time:
        if isinstance(data, str):
            return datetime.time.fromisoformat(data)
        else:
            raise ValueError(f"Cannot convert {data} to time")
    
    # Handle UUID
    if target_type is uuid.UUID:
        if isinstance(data, str):
            return uuid.UUID(data)
        else:
            raise ValueError(f"Cannot convert {data} to UUID")
    
    # Handle Decimal
    if target_type is decimal.Decimal:
        if isinstance(data, (int, float, str)):
            return decimal.Decimal(data)
        else:
            raise ValueError(f"Cannot convert {data} to Decimal")
    
    # Handle dataclasses
    if is_dataclass(target_type):
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict for dataclass, got {type(data)}")
        
        # Get the field types
        field_types = t.get_type_hints(target_type)
        
        # Deserialize each field
        kwargs = {}
        for field_name, field_type in field_types.items():
            if field_name in data:
                kwargs[field_name] = deserialize(data[field_name], field_type)
        
        # Create the dataclass instance
        return target_type(**kwargs)
    
    # If we get here, we don't know how to deserialize the data
    return data


def serialize_response(result: t.Any) -> t.Any:
    """
    Serialize a function result for an API response.
    
    Args:
        result: The function result to serialize.
        
    Returns:
        A JSON-compatible representation of the result.
    """
    return serialize(result)


def deserialize_params(
    params: t.Dict[str, t.Any],
    func: t.Union[t.Callable, inspect.Signature],
    type_hints: t.Optional[t.Dict[str, t.Type]] = None
) -> t.Dict[str, t.Any]:
    """
    Deserialize parameters for a function call.
    
    Args:
        params: The parameters to deserialize.
        func: The function or signature to deserialize parameters for.
        type_hints: Optional type hints. If not provided, they will be extracted from the function.
        
    Returns:
        The deserialized parameters.
    """
    # Get the function signature
    if isinstance(func, inspect.Signature):
        signature = func
    else:
        signature = inspect.signature(func)
    
    # Get type hints if not provided
    if type_hints is None and not isinstance(func, inspect.Signature):
        type_hints = t.get_type_hints(func)
    
    if type_hints is None:
        raise ValueError("Type hints must be provided when using a signature object")
    
    result = {}
    
    for param_name, param in signature.parameters.items():
        # Skip self, cls, and **kwargs
        if param_name in ("self", "cls") or param.kind == param.VAR_KEYWORD:
            continue
        
        # Special case for 'request' parameter
        if param_name == "request" and param_name not in params:
            # The request parameter is handled separately by the wrapper
            continue
        
        # Get the parameter value
        if param_name in params:
            value = params[param_name]
        elif param.default is not param.empty:
            # Use default value
            continue
        else:
            # Missing required parameter
            raise ValueError(f"Missing required parameter: {param_name}")
        
        # Get the parameter type
        param_type = type_hints.get(param_name, t.Any)
        
        # Try to parse JSON strings for collection types
        if isinstance(value, str) and value.strip():
            try:
                if (hasattr(param_type, "__origin__") and 
                    param_type.__origin__ in (list, dict, set, tuple) and
                    (value.startswith('[') and value.endswith(']') or
                     value.startswith('{') and value.endswith('}'))):
                    value = json.loads(value)
            except json.JSONDecodeError:
                # Not valid JSON, use as is
                pass
        
        # Deserialize the parameter
        try:
            result[param_name] = deserialize(value, param_type)
        except ValueError as e:
            raise ValueError(f"Invalid value for parameter {param_name}: {e}")
    
    return result 