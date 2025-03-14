"""
Type utilities for APIFromAnything.

This module provides utilities for working with Python types and type hints.
"""

import inspect
import logging
import sys
import typing as t
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def get_type_hints_with_extras(obj: t.Callable) -> t.Dict[str, t.Type]:
    """
    Get type hints for a callable, including return type.
    
    This function extends typing.get_type_hints to include additional information
    about the types, such as whether they are optional.
    
    Args:
        obj: The callable to get type hints for.
        
    Returns:
        A dictionary mapping parameter names to their types.
    """
    try:
        hints = t.get_type_hints(obj)
    except (TypeError, ValueError, NameError) as e:
        logger.warning(f"Failed to get type hints for {obj.__name__}: {e}")
        hints = {}
    
    # Add information about optional parameters
    sig = inspect.signature(obj)
    for param_name, param in sig.parameters.items():
        if param_name not in hints:
            continue
        
        # If parameter has a default value, it's optional
        if param.default is not param.empty:
            # Make the type Optional if it's not already
            param_type = hints[param_name]
            if not is_optional(param_type):
                hints[param_name] = t.Optional[param_type]
    
    return hints


def is_optional(type_hint: t.Type) -> bool:
    """
    Check if a type hint is Optional.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is Optional, False otherwise.
    """
    origin = t.get_origin(type_hint)
    args = t.get_args(type_hint)
    
    # Check if it's Union[T, None]
    return origin is t.Union and type(None) in args


def get_origin_type(type_hint: t.Type) -> t.Type:
    """
    Get the origin type of a type hint.
    
    For generic types like List[int], this returns List.
    For Optional types like Optional[int], this returns Union.
    
    Args:
        type_hint: The type hint to get the origin type for.
        
    Returns:
        The origin type.
    """
    origin = t.get_origin(type_hint)
    args = t.get_args(type_hint)
    
    # Handle Optional types
    if origin is t.Union and type(None) in args:
        return type(t.Union)
    
    # Handle other generic types
    if origin is not None:
        return origin
    
    # Not a generic type
    return type_hint


def get_inner_type(type_hint: t.Type) -> t.Type:
    """
    Get the inner type of a generic type hint.
    
    For types like List[int], this returns int.
    For types like Dict[str, int], this returns (str, int).
    
    Args:
        type_hint: The type hint to get the inner type for.
        
    Returns:
        The inner type, or a tuple of inner types for Dict.
    """
    origin = t.get_origin(type_hint)
    args = t.get_args(type_hint)
    
    # Handle Optional types
    if origin is t.Union and type(None) in args:
        # Find the non-None type
        for arg in args:
            if arg is not type(None):
                return get_inner_type(arg)
    
    # Handle other generic types
    if args:
        if len(args) == 1:
            return args[0]
        else:
            # Convert tuple of types to a tuple type for type compatibility
            return type(args)
    
    # Not a generic type
    return type_hint


def is_builtin_type(type_hint: t.Type) -> bool:
    """
    Check if a type hint is a builtin type.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is a builtin type, False otherwise.
    """
    if type_hint in (str, int, float, bool, list, dict, set, tuple, bytes, bytearray):
        return True
    
    # Handle generic types
    origin = get_origin_type(type_hint)
    return origin in (list, dict, set, tuple, t.List, t.Dict, t.Set, t.Tuple)


def is_json_serializable(type_hint: t.Type) -> bool:
    """
    Check if a type hint is JSON serializable.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is JSON serializable, False otherwise.
    """
    # Handle None
    if type_hint is type(None):
        return True
    
    # Handle Optional types
    if is_optional(type_hint):
        # Check the non-None type
        inner_type = get_inner_type(type_hint)
        return is_json_serializable(inner_type)
    
    # Handle builtin types
    if type_hint in (str, int, float, bool, list, dict, tuple, set):
        return True
    
    # Handle generic types
    origin = t.get_origin(type_hint)
    args = t.get_args(type_hint)
    
    if origin in (list, t.List, tuple, t.Tuple, set, t.Set):
        # Check the inner type
        if not args:
            return True
        if len(args) == 2 and args[1] is Ellipsis:  # Handle Tuple[T, ...]
            return is_json_serializable(args[0])
        if origin in (tuple, t.Tuple):  # Handle Tuple[T1, T2, ...]
            return all(is_json_serializable(arg) for arg in args)
        return is_json_serializable(args[0])
    
    if origin in (dict, t.Dict):
        # Check the key and value types
        if not args:
            return True
        key_type, value_type = args
        return (key_type is str or key_type is int) and is_json_serializable(value_type)
    
    # Not JSON serializable
    return False

# Add the missing functions required by openapi.py

def get_args(type_hint: t.Type) -> t.Tuple[t.Type, ...]:
    """
    Get the arguments of a type hint.
    
    For types like List[int], this returns (int,).
    For types like Dict[str, int], this returns (str, int).
    
    Args:
        type_hint: The type hint to get the arguments for.
        
    Returns:
        A tuple of type arguments.
    """
    return t.get_args(type_hint)

def get_origin(type_hint: t.Type) -> t.Optional[t.Type]:
    """
    Get the origin of a type hint.
    
    For types like List[int], this returns List.
    For types like Dict[str, int], this returns Dict.
    
    Args:
        type_hint: The type hint to get the origin for.
        
    Returns:
        The origin type, or None if not a generic type.
    """
    return t.get_origin(type_hint)

def is_optional_type(type_hint: t.Type) -> bool:
    """
    Check if a type hint is Optional.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is Optional, False otherwise.
    """
    return is_optional(type_hint)

def extract_optional_type(type_hint: t.Type) -> t.Type:
    """
    Extract the inner type from an Optional type hint.
    
    For types like Optional[int], this returns int.
    
    Args:
        type_hint: The type hint to extract from.
        
    Returns:
        The inner type.
    """
    if not is_optional_type(type_hint):
        return type_hint
    
    args = get_args(type_hint)
    for arg in args:
        if arg is not type(None):
            return arg
    
    return type_hint

def is_list_type(type_hint: t.Type) -> bool:
    """
    Check if a type hint is a list type.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is a list type, False otherwise.
    """
    origin = get_origin(type_hint)
    return origin in (list, t.List)

def is_dict_type(type_hint: t.Type) -> bool:
    """
    Check if a type hint is a dictionary type.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is a dictionary type, False otherwise.
    """
    origin = get_origin(type_hint)
    return origin in (dict, t.Dict)

def is_union_type(type_hint: t.Type) -> bool:
    """
    Check if a type hint is a Union type.
    
    Args:
        type_hint: The type hint to check.
        
    Returns:
        True if the type hint is a Union type, False otherwise.
    """
    origin = get_origin(type_hint)
    return origin is t.Union

def get_union_types(type_hint: t.Type) -> t.List[t.Type]:
    """
    Get the types in a Union type hint.
    
    Args:
        type_hint: The type hint to get the types from.
        
    Returns:
        A list of types in the Union.
    """
    if not is_union_type(type_hint):
        return [type_hint]
    
    return list(get_args(type_hint)) 