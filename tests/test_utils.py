"""
Tests for the APIFromAnything utils module.

This module tests the functionality of utility components in apifrom.utils.
"""

import unittest
import json
import enum
import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any, Tuple, Set

import pytest

from apifrom.utils.serialization import (
    JSONEncoder,
    serialize,
    deserialize,
    serialize_response,
    deserialize_params
)
from apifrom.utils.type_utils import (
    get_type_hints_with_extras,
    is_optional,
    get_origin_type,
    get_inner_type,
    is_builtin_type,
    is_json_serializable
)


# Test data for serialization and deserialization tests
class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass
class Person:
    name: str
    age: int
    favorite_color: Optional[Color] = None


@dataclass
class Address:
    street: str
    city: str
    zip_code: str


@dataclass
class Employee:
    name: str
    age: int
    job_title: str
    salary: float
    address: Address
    favorite_color: Optional[Color] = None


class TestSerialization(unittest.TestCase):
    """Test serialization utilities."""
    
    def test_serialize_primitive_types(self):
        """Test serialization of primitive types."""
        self.assertEqual(serialize(42), 42)
        self.assertEqual(serialize(3.14), 3.14)
        self.assertEqual(serialize("hello"), "hello")
        self.assertEqual(serialize(True), True)
        self.assertEqual(serialize(None), None)
    
    def test_serialize_collections(self):
        """Test serialization of collection types."""
        self.assertEqual(serialize([1, 2, 3]), [1, 2, 3])
        self.assertEqual(serialize({"a": 1, "b": 2}), {"a": 1, "b": 2})
        self.assertEqual(serialize((1, 2, 3)), [1, 2, 3])
        self.assertEqual(serialize({1, 2, 3}), [1, 2, 3])
    
    def test_serialize_enum(self):
        """Test serialization of enum types."""
        self.assertEqual(serialize(Color.RED), "red")
        self.assertEqual(serialize(Color.GREEN), "green")
        self.assertEqual(serialize(Color.BLUE), "blue")
    
    def test_serialize_dataclass(self):
        """Test serialization of dataclass types."""
        person = Person(name="John", age=30, favorite_color=Color.BLUE)
        
        expected = {
            "name": "John",
            "age": 30,
            "favorite_color": "blue"
        }
        
        self.assertEqual(serialize(person), expected)
    
    def test_serialize_nested_dataclass(self):
        """Test serialization of nested dataclass types."""
        address = Address(street="123 Main St", city="Anytown", zip_code="12345")
        employee = Employee(
            name="Jane",
            age=35,
            job_title="Developer",
            salary=100000.0,
            address=address,
            favorite_color=Color.BLUE
        )
        
        expected = {
            "name": "Jane",
            "age": 35,
            "favorite_color": "blue",
            "job_title": "Developer",
            "salary": 100000.0,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zip_code": "12345"
            }
        }
        
        self.assertEqual(serialize(employee), expected)
    
    def test_serialize_complex_structure(self):
        """Test serialization of a complex nested structure."""
        address1 = Address(street="123 Main St", city="Anytown", zip_code="12345")
        address2 = Address(street="456 Oak Ave", city="Othertown", zip_code="67890")
        
        employee1 = Employee(
            name="Alice",
            age=30,
            job_title="Developer",
            salary=100000.0,
            address=address1,
            favorite_color=Color.RED
        )
        
        employee2 = Employee(
            name="Bob",
            age=40,
            job_title="Manager",
            salary=150000.0,
            address=address2,
            favorite_color=Color.GREEN
        )
        
        data = {
            "employees": [employee1, employee2],
            "departments": {"dev": [employee1], "management": [employee2]},
            "stats": {
                "average_age": 35,
                "total_salary": 250000.0
            }
        }
        
        expected = {
            "employees": [
                {
                    "name": "Alice",
                    "age": 30,
                    "favorite_color": "red",
                    "job_title": "Developer",
                    "salary": 100000.0,
                    "address": {
                        "street": "123 Main St",
                        "city": "Anytown",
                        "zip_code": "12345"
                    }
                },
                {
                    "name": "Bob",
                    "age": 40,
                    "favorite_color": "green",
                    "job_title": "Manager",
                    "salary": 150000.0,
                    "address": {
                        "street": "456 Oak Ave",
                        "city": "Othertown",
                        "zip_code": "67890"
                    }
                }
            ],
            "departments": {
                "dev": [
                    {
                        "name": "Alice",
                        "age": 30,
                        "favorite_color": "red",
                        "job_title": "Developer",
                        "salary": 100000.0,
                        "address": {
                            "street": "123 Main St",
                            "city": "Anytown",
                            "zip_code": "12345"
                        }
                    }
                ],
                "management": [
                    {
                        "name": "Bob",
                        "age": 40,
                        "favorite_color": "green",
                        "job_title": "Manager",
                        "salary": 150000.0,
                        "address": {
                            "street": "456 Oak Ave",
                            "city": "Othertown",
                            "zip_code": "67890"
                        }
                    }
                ]
            },
            "stats": {
                "average_age": 35,
                "total_salary": 250000.0
            }
        }
        
        self.assertEqual(serialize(data), expected)
    
    def test_json_encoder(self):
        """Test the JSONEncoder class."""
        person = Person(name="John", age=30, favorite_color=Color.BLUE)
        
        # Use the encoder directly with json.dumps
        json_str = json.dumps(person, cls=JSONEncoder)
        expected = '{"name": "John", "age": 30, "favorite_color": "blue"}'
        
        # Compare as dictionaries to avoid issues with whitespace
        self.assertEqual(json.loads(json_str), json.loads(expected))
    
    def test_date_time_serialization(self):
        """Test serialization of datetime objects."""
        # Test date
        date = datetime.date(2023, 1, 1)
        self.assertEqual(serialize(date), "2023-01-01")
        
        # Test time
        time = datetime.time(12, 30, 45)
        self.assertEqual(serialize(time), "12:30:45")
        
        # Test datetime
        dt = datetime.datetime(2023, 1, 1, 12, 30, 45)
        self.assertEqual(serialize(dt), "2023-01-01T12:30:45")
    
    def test_serialize_response(self):
        """Test the serialize_response function."""
        # Test with a simple value
        self.assertEqual(serialize_response(42), 42)
        
        # Test with a complex object
        person = Person(name="John", age=30, favorite_color=Color.BLUE)
        expected = {
            "name": "John",
            "age": 30,
            "favorite_color": "blue"
        }
        self.assertEqual(serialize_response(person), expected)


class TestDeserialization(unittest.TestCase):
    """Test deserialization utilities."""
    
    def test_deserialize_primitive_types(self):
        """Test deserialization of primitive types."""
        self.assertEqual(deserialize(42, int), 42)
        self.assertEqual(deserialize(3.14, float), 3.14)
        self.assertEqual(deserialize("hello", str), "hello")
        self.assertEqual(deserialize(True, bool), True)
        self.assertEqual(deserialize(None, type(None)), None)
    
    def test_deserialize_collections(self):
        """Test deserialization of collection types."""
        # List
        self.assertEqual(deserialize([1, 2, 3], List[int]), [1, 2, 3])
        
        # Dict
        self.assertEqual(deserialize({"a": 1, "b": 2}, Dict[str, int]), {"a": 1, "b": 2})
        
        # Tuple
        self.assertEqual(deserialize([1, 2, 3], Tuple[int, int, int]), (1, 2, 3))
        
        # Set
        self.assertEqual(deserialize([1, 2, 3], Set[int]), {1, 2, 3})
    
    def test_deserialize_enum(self):
        """Test deserialization of enum types."""
        self.assertEqual(deserialize("red", Color), Color.RED)
        self.assertEqual(deserialize("green", Color), Color.GREEN)
        self.assertEqual(deserialize("blue", Color), Color.BLUE)
    
    def test_deserialize_dataclass(self):
        """Test deserialization of dataclass types."""
        data = {
            "name": "John",
            "age": 30,
            "favorite_color": "blue"
        }
        
        expected = Person(name="John", age=30, favorite_color=Color.BLUE)
        result = deserialize(data, Person)
        
        self.assertEqual(result.name, expected.name)
        self.assertEqual(result.age, expected.age)
        self.assertEqual(result.favorite_color, expected.favorite_color)
    
    def test_deserialize_nested_dataclass(self):
        """Test deserialization of nested dataclass types."""
        data = {
            "name": "Jane",
            "age": 35,
            "job_title": "Developer",
            "salary": 100000.0,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zip_code": "12345"
            },
            "favorite_color": "blue"
        }
        
        result = deserialize(data, Employee)
        
        self.assertEqual(result.name, "Jane")
        self.assertEqual(result.age, 35)
        self.assertEqual(result.job_title, "Developer")
        self.assertEqual(result.salary, 100000.0)
        self.assertEqual(result.address.street, "123 Main St")
        self.assertEqual(result.address.city, "Anytown")
        self.assertEqual(result.address.zip_code, "12345")
        self.assertEqual(result.favorite_color, Color.BLUE)
    
    def test_deserialize_optional(self):
        """Test deserialization of Optional types."""
        # Test with a value
        self.assertEqual(deserialize(42, Optional[int]), 42)
        
        # Test with None
        self.assertEqual(deserialize(None, Optional[int]), None)
    
    def test_deserialize_union(self):
        """Test deserialization of Union types."""
        # Test with int
        self.assertEqual(deserialize(42, Union[int, str]), 42)
        
        # Test with str
        self.assertEqual(deserialize("hello", Union[int, str]), "hello")
    
    def test_deserialize_params(self):
        """Test the deserialize_params function."""
        # Define a function with various parameter types
        def test_func(
            a: int,
            b: str,
            c: Optional[float] = None,
            d: List[int] = None,
            e: Dict[str, Any] = None
        ):
            pass
        
        # Test deserializing parameters
        params = {
            "a": "42",  # Will be converted to int
            "b": "hello",
            "c": "3.14",  # Will be converted to float
            "d": "[1, 2, 3]",  # Will be parsed as JSON
            "e": '{"x": 1, "y": 2}'  # Will be parsed as JSON
        }
        
        result = deserialize_params(params, test_func)
        
        self.assertEqual(result["a"], 42)
        self.assertEqual(result["b"], "hello")
        self.assertEqual(result["c"], 3.14)
        self.assertEqual(result["d"], [1, 2, 3])
        self.assertEqual(result["e"], {"x": 1, "y": 2})


class TestTypeUtils(unittest.TestCase):
    """Test type utility functions."""
    
    def test_is_optional(self):
        """Test the is_optional function."""
        self.assertTrue(is_optional(Optional[int]))
        self.assertTrue(is_optional(Union[int, None]))
        self.assertTrue(is_optional(Union[None, int]))
        self.assertFalse(is_optional(int))
        self.assertFalse(is_optional(Union[int, str]))
    
    def test_get_origin_type(self):
        """Test the get_origin_type function."""
        self.assertEqual(get_origin_type(int), int)
        self.assertEqual(get_origin_type(List[int]), list)
        self.assertEqual(get_origin_type(Dict[str, int]), dict)
        self.assertEqual(get_origin_type(Optional[int]), Union)
        self.assertEqual(get_origin_type(Union[int, str]), Union)
    
    def test_get_inner_type(self):
        """Test the get_inner_type function."""
        self.assertEqual(get_inner_type(int), int)
        self.assertEqual(get_inner_type(List[int]), int)
        self.assertEqual(get_inner_type(Dict[str, int]), (str, int))
        self.assertEqual(get_inner_type(Optional[int]), int)
        self.assertEqual(get_inner_type(Union[int, str]), (int, str))
    
    def test_is_builtin_type(self):
        """Test the is_builtin_type function."""
        self.assertTrue(is_builtin_type(int))
        self.assertTrue(is_builtin_type(float))
        self.assertTrue(is_builtin_type(str))
        self.assertTrue(is_builtin_type(bool))
        self.assertTrue(is_builtin_type(list))
        self.assertTrue(is_builtin_type(dict))
        self.assertTrue(is_builtin_type(tuple))
        self.assertTrue(is_builtin_type(set))
        self.assertFalse(is_builtin_type(Person))
        self.assertFalse(is_builtin_type(Color))
    
    def test_is_json_serializable(self):
        """Test the is_json_serializable function."""
        self.assertTrue(is_json_serializable(int))
        self.assertTrue(is_json_serializable(float))
        self.assertTrue(is_json_serializable(str))
        self.assertTrue(is_json_serializable(bool))
        self.assertTrue(is_json_serializable(list))
        self.assertTrue(is_json_serializable(dict))
        
        # Complex types might not be directly JSON serializable
        self.assertFalse(is_json_serializable(Person))
        self.assertFalse(is_json_serializable(Color))


if __name__ == "__main__":
    unittest.main() 