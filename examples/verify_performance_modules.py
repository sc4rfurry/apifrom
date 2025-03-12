"""
Verification script for performance optimization modules.

This script verifies that all performance optimization modules are working correctly
by importing and instantiating key classes.
"""

import os
import sys
import importlib

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check_module(module_name, classes):
    """
    Check if a module can be imported and its classes instantiated.
    
    Args:
        module_name: The name of the module to check
        classes: List of class names to check
        
    Returns:
        A tuple of (success, error_message)
    """
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported module: {module_name}")
        
        for class_name in classes:
            try:
                cls = getattr(module, class_name)
                instance = cls()
                print(f"  ✅ Successfully instantiated class: {class_name}")
            except Exception as e:
                print(f"  ❌ Failed to instantiate class: {class_name}")
                print(f"     Error: {str(e)}")
                return False, f"Failed to instantiate class {class_name}: {str(e)}"
        
        return True, None
    except Exception as e:
        print(f"❌ Failed to import module: {module_name}")
        print(f"   Error: {str(e)}")
        return False, f"Failed to import module {module_name}: {str(e)}"

def main():
    """Run the verification for all performance modules."""
    print("Verifying performance optimization modules...")
    print("-" * 50)
    
    # Define modules and classes to check
    modules_to_check = [
        ("apifrom.performance.profiler", ["APIProfiler", "ProfileReport"]),
        ("apifrom.performance.cache_optimizer", ["CacheOptimizer", "CacheAnalytics"]),
        ("apifrom.performance.connection_pool", ["ConnectionPool", "ConnectionPoolMetrics"]),
        ("apifrom.performance.optimization", ["OptimizationConfig", "OptimizationAnalyzer", "Web"]),
        ("apifrom.middleware.cache_advanced", ["MemoryCacheBackend", "AdvancedCacheMiddleware"])
    ]
    
    middleware_classes = [
        ("apifrom.performance.profiler", "ProfileMiddleware"),
        ("apifrom.performance.cache_optimizer", "OptimizedCacheMiddleware"),
        ("apifrom.performance.connection_pool", "ConnectionPoolMiddleware"),
    ]
    
    # Check each module
    all_success = True
    for module_name, classes in modules_to_check:
        success, error = check_module(module_name, classes)
        if not success:
            all_success = False
        print()
    
    # Verify Web decorator
    try:
        from apifrom.performance.optimization import Web
        
        @Web.optimize(cache_ttl=30, profile=True)
        def test_function():
            return "Hello, World!"
        
        result = test_function()
        print(f"✅ Successfully applied Web.optimize decorator")
        print(f"  Result: {result}")
        print(f"  Optimization config: {Web.get_optimization_config(test_function)}")
    except Exception as e:
        all_success = False
        print(f"❌ Failed to apply Web.optimize decorator")
        print(f"   Error: {str(e)}")
    
    print("-" * 50)
    if all_success:
        print("✅ All performance optimization modules verified successfully!")
    else:
        print("❌ Some verifications failed. Please check the output above.")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main()) 