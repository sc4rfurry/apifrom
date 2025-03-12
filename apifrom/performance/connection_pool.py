"""
Connection pooling utilities for APIFromAnything.

This module provides tools for efficient connection management in high-load scenarios,
including connection pooling, monitoring, and optimization.
"""

import time
import threading
import asyncio
from typing import Dict, List, Optional, Callable, Any, Union, Tuple, Set
import logging
import json
import os
from datetime import datetime
import importlib
from contextlib import asynccontextmanager, contextmanager

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


# Set up logging
logger = logging.getLogger("apifrom.performance.connection_pool")


class ConnectionPoolMetrics:
    """
    Collects and analyzes connection pool metrics.
    
    This class collects connection pool metrics such as pool size,
    connection acquisition times, and utilization, and provides
    tools for analyzing and visualizing this data.
    """
    
    def __init__(self):
        """
        Initialize connection pool metrics.
        """
        self._lock = threading.Lock()
        self.reset()
    
    def reset(self):
        """
        Reset all metrics data.
        """
        with self._lock:
            self.start_time = time.time()
            self.total_connections = 0
            self.active_connections = 0
            self.idle_connections = 0
            self.max_connections = 0
            self.connection_requests = 0
            self.connection_timeouts = 0
            self.connection_errors = 0
            self.acquisition_times = []
            self.release_times = []
            self.connection_lifetimes = {}
    
    def record_connection_request(self):
        """
        Record a connection request.
        """
        with self._lock:
            self.connection_requests += 1
    
    def record_connection_acquire(self, connection_id: str, acquisition_time: float):
        """
        Record a connection acquisition.
        
        Args:
            connection_id: The connection ID
            acquisition_time: The time it took to acquire the connection in seconds
        """
        with self._lock:
            self.total_connections = max(self.total_connections, len(self.connection_lifetimes) + 1)
            self.active_connections += 1
            self.idle_connections = max(0, self.total_connections - self.active_connections)
            self.max_connections = max(self.max_connections, self.active_connections)
            self.acquisition_times.append(acquisition_time * 1000)  # Convert to ms
            self.connection_lifetimes[connection_id] = time.time()
    
    def record_connection_release(self, connection_id: str, release_time: float):
        """
        Record a connection release.
        
        Args:
            connection_id: The connection ID
            release_time: The time it took to release the connection in seconds
        """
        with self._lock:
            self.active_connections = max(0, self.active_connections - 1)
            self.idle_connections = max(0, self.total_connections - self.active_connections)
            self.release_times.append(release_time * 1000)  # Convert to ms
            
            if connection_id in self.connection_lifetimes:
                lifetime = time.time() - self.connection_lifetimes[connection_id]
                del self.connection_lifetimes[connection_id]
    
    def record_connection_timeout(self):
        """
        Record a connection timeout.
        """
        with self._lock:
            self.connection_timeouts += 1
    
    def record_connection_error(self):
        """
        Record a connection error.
        """
        with self._lock:
            self.connection_errors += 1
    
    @property
    def avg_acquisition_time(self) -> float:
        """
        Get the average connection acquisition time in milliseconds.
        
        Returns:
            The average acquisition time
        """
        with self._lock:
            if not self.acquisition_times:
                return 0.0
            return sum(self.acquisition_times) / len(self.acquisition_times)
    
    @property
    def avg_release_time(self) -> float:
        """
        Get the average connection release time in milliseconds.
        
        Returns:
            The average release time
        """
        with self._lock:
            if not self.release_times:
                return 0.0
            return sum(self.release_times) / len(self.release_times)
    
    @property
    def pool_utilization(self) -> float:
        """
        Get the pool utilization ratio (active connections / total connections).
        
        Returns:
            The pool utilization ratio (0.0 to 1.0)
        """
        with self._lock:
            if self.total_connections == 0:
                return 0.0
            return self.active_connections / self.total_connections
    
    @property
    def error_rate(self) -> float:
        """
        Get the connection error rate.
        
        Returns:
            The error rate (0.0 to 1.0)
        """
        with self._lock:
            if self.connection_requests == 0:
                return 0.0
            return (self.connection_timeouts + self.connection_errors) / self.connection_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the metrics data to a dictionary.
        
        Returns:
            A dictionary representation of the metrics data
        """
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": time.time() - self.start_time,
                "total_connections": self.total_connections,
                "active_connections": self.active_connections,
                "idle_connections": self.idle_connections,
                "max_connections": self.max_connections,
                "connection_requests": self.connection_requests,
                "connection_timeouts": self.connection_timeouts,
                "connection_errors": self.connection_errors,
                "avg_acquisition_time_ms": self.avg_acquisition_time,
                "avg_release_time_ms": self.avg_release_time,
                "pool_utilization": self.pool_utilization,
                "error_rate": self.error_rate,
            }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert the metrics data to a JSON string.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            A JSON string representation of the metrics data
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """
        Save the metrics data to a file.
        
        Args:
            file_path: The path to save the data to
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def print_summary(self) -> None:
        """
        Print a summary of the metrics data to the console.
        """
        print("=== Connection Pool Metrics Summary ===")
        print(f"Duration: {time.time() - self.start_time:.2f} seconds")
        print(f"Total Connections: {self.total_connections}")
        print(f"Active Connections: {self.active_connections}")
        print(f"Idle Connections: {self.idle_connections}")
        print(f"Max Connections: {self.max_connections}")
        print(f"Connection Requests: {self.connection_requests}")
        print(f"Connection Timeouts: {self.connection_timeouts}")
        print(f"Connection Errors: {self.connection_errors}")
        print(f"Average Acquisition Time: {self.avg_acquisition_time:.2f} ms")
        print(f"Average Release Time: {self.avg_release_time:.2f} ms")
        print(f"Pool Utilization: {self.pool_utilization:.2%}")
        print(f"Error Rate: {self.error_rate:.2%}")


class ConnectionPoolSettings:
    """
    Settings for a connection pool.
    
    This class defines the settings for a connection pool,
    such as pool size, timeout, and retry parameters.
    """
    
    def __init__(self,
                 min_size: int = 1,
                 max_size: int = 10,
                 max_idle: int = 5,
                 max_lifetime: int = 3600,
                 acquire_timeout: float = 10.0,
                 idle_timeout: float = 300.0,
                 retry_limit: int = 3,
                 retry_delay: float = 1.0,
                 validate_on_acquire: bool = True):
        """
        Initialize connection pool settings.
        
        Args:
            min_size: The minimum pool size
            max_size: The maximum pool size
            max_idle: The maximum number of idle connections
            max_lifetime: The maximum connection lifetime in seconds
            acquire_timeout: The connection acquisition timeout in seconds
            idle_timeout: The idle connection timeout in seconds
            retry_limit: The maximum number of connection retries
            retry_delay: The delay between connection retries in seconds
            validate_on_acquire: Whether to validate connections on acquisition
        """
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle = max_idle
        self.max_lifetime = max_lifetime
        self.acquire_timeout = acquire_timeout
        self.idle_timeout = idle_timeout
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.validate_on_acquire = validate_on_acquire
    
    @classmethod
    def create_aggressive(cls) -> 'ConnectionPoolSettings':
        """
        Create aggressive connection pool settings.
        
        These settings are optimized for high-throughput, low-latency scenarios.
        
        Returns:
            ConnectionPoolSettings instance
        """
        return cls(
            min_size=10,
            max_size=100,
            max_idle=20,
            max_lifetime=1800,  # 30 minutes
            acquire_timeout=5.0,
            idle_timeout=600.0,  # 10 minutes
            retry_limit=5,
            retry_delay=0.1,
            validate_on_acquire=False
        )
    
    @classmethod
    def create_conservative(cls) -> 'ConnectionPoolSettings':
        """
        Create conservative connection pool settings.
        
        These settings are optimized for reliability and resource efficiency.
        
        Returns:
            ConnectionPoolSettings instance
        """
        return cls(
            min_size=1,
            max_size=5,
            max_idle=2,
            max_lifetime=7200,  # 2 hours
            acquire_timeout=30.0,
            idle_timeout=1800.0,  # 30 minutes
            retry_limit=3,
            retry_delay=1.0,
            validate_on_acquire=True
        )
    
    @classmethod
    def create_balanced(cls) -> 'ConnectionPoolSettings':
        """
        Create balanced connection pool settings.
        
        These settings provide a balance between performance and resource usage.
        
        Returns:
            ConnectionPoolSettings instance
        """
        return cls(
            min_size=5,
            max_size=20,
            max_idle=10,
            max_lifetime=3600,  # 1 hour
            acquire_timeout=10.0,
            idle_timeout=300.0,  # 5 minutes
            retry_limit=3,
            retry_delay=0.5,
            validate_on_acquire=True
        )


class ConnectionPool:
    """
    A generic connection pool for managing connections to external resources.
    
    This class provides a pool of connections to external resources,
    such as databases, APIs, or services, and manages their lifecycle.
    """
    
    def __init__(self,
                 factory: Callable[[], Any],
                 settings: Optional[ConnectionPoolSettings] = None,
                 validate_func: Optional[Callable[[Any], bool]] = None,
                 close_func: Optional[Callable[[Any], None]] = None,
                 metrics: Optional[ConnectionPoolMetrics] = None):
        """
        Initialize a connection pool.
        
        Args:
            factory: A factory function that creates new connections
            settings: The connection pool settings
            validate_func: A function that validates connections
            close_func: A function that closes connections
            metrics: A metrics instance for collecting pool metrics
        """
        self.factory = factory
        self.settings = settings or ConnectionPoolSettings()
        self.validate_func = validate_func or (lambda conn: True)
        self.close_func = close_func or (lambda conn: None)
        self.metrics = metrics or ConnectionPoolMetrics()
        
        self._pool = asyncio.Queue(maxsize=self.settings.max_size)
        self._active_connections = set()
        self._connection_lifetimes = {}
        self._lock = asyncio.Lock()
        self._closed = False
    
    async def _create_connection(self) -> Any:
        """
        Create a new connection.
        
        Returns:
            A new connection
        """
        connection = await self.factory()
        connection_id = id(connection)
        self._connection_lifetimes[connection_id] = time.time()
        return connection
    
    async def _validate_connection(self, connection: Any) -> bool:
        """
        Validate a connection.
        
        Args:
            connection: The connection to validate
            
        Returns:
            True if the connection is valid, False otherwise
        """
        try:
            # Check if the connection has expired
            connection_id = id(connection)
            if connection_id in self._connection_lifetimes:
                lifetime = time.time() - self._connection_lifetimes[connection_id]
                if lifetime > self.settings.max_lifetime:
                    logger.debug(f"Connection {connection_id} has exceeded its maximum lifetime")
                    return False
            
            # Validate the connection
            if callable(self.validate_func):
                return await self.validate_func(connection)
            return True
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False
    
    async def _close_connection(self, connection: Any) -> None:
        """
        Close a connection.
        
        Args:
            connection: The connection to close
        """
        try:
            connection_id = id(connection)
            if connection_id in self._connection_lifetimes:
                del self._connection_lifetimes[connection_id]
            
            if callable(self.close_func):
                await self.close_func(connection)
        except Exception as e:
            logger.warning(f"Connection close failed: {e}")
    
    async def initialize(self) -> None:
        """
        Initialize the connection pool.
        
        This method creates the minimum number of connections.
        """
        async with self._lock:
            for _ in range(self.settings.min_size):
                try:
                    connection = await self._create_connection()
                    await self._pool.put(connection)
                except Exception as e:
                    logger.warning(f"Failed to create initial connection: {e}")
    
    async def acquire(self) -> Any:
        """
        Acquire a connection from the pool.
        
        Returns:
            A connection from the pool
        
        Raises:
            TimeoutError: If no connection could be acquired within the timeout
            RuntimeError: If the pool is closed
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        # Record connection request
        self.metrics.record_connection_request()
        
        # Measure acquisition time
        start_time = time.time()
        
        # Try to get a connection from the pool
        try:
            connection = None
            
            # Try to get a connection from the pool
            try:
                connection = await asyncio.wait_for(
                    self._pool.get(),
                    timeout=self.settings.acquire_timeout
                )
            except asyncio.TimeoutError:
                # Pool is empty and max size not reached, create a new connection
                async with self._lock:
                    if len(self._active_connections) < self.settings.max_size:
                        connection = await self._create_connection()
                    else:
                        self.metrics.record_connection_timeout()
                        raise TimeoutError("Connection pool timeout")
            
            # Validate the connection if required
            if self.settings.validate_on_acquire and not await self._validate_connection(connection):
                # Connection is invalid, close it and create a new one
                await self._close_connection(connection)
                connection = await self._create_connection()
            
            # Record connection acquisition
            connection_id = id(connection)
            self._active_connections.add(connection_id)
            acquisition_time = time.time() - start_time
            self.metrics.record_connection_acquire(str(connection_id), acquisition_time)
            
            return connection
        except Exception as e:
            # Record connection error
            self.metrics.record_connection_error()
            logger.error(f"Failed to acquire connection: {e}")
            raise
    
    async def release(self, connection: Any) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        if self._closed:
            await self._close_connection(connection)
            return
        
        # Measure release time
        start_time = time.time()
        
        connection_id = id(connection)
        
        # Remove connection from active connections
        self._active_connections.discard(connection_id)
        
        # Check if the connection is valid
        if await self._validate_connection(connection):
            # Check if we have too many idle connections
            if self._pool.qsize() >= self.settings.max_idle:
                # Too many idle connections, close this one
                await self._close_connection(connection)
            else:
                # Return the connection to the pool
                await self._pool.put(connection)
        else:
            # Connection is invalid, close it
            await self._close_connection(connection)
        
        # Record connection release
        release_time = time.time() - start_time
        self.metrics.record_connection_release(str(connection_id), release_time)
    
    @asynccontextmanager
    async def connection(self):
        """
        Get a connection from the pool as a context manager.
        
        This method acquires a connection from the pool, yields it,
        and ensures it is released back to the pool when done.
        
        Yields:
            A connection from the pool
        """
        connection = await self.acquire()
        try:
            yield connection
        finally:
            await self.release(connection)
    
    async def close(self) -> None:
        """
        Close the connection pool.
        
        This method closes all connections in the pool.
        """
        if self._closed:
            return
        
        self._closed = True
        
        # Close all connections in the pool
        while not self._pool.empty():
            connection = await self._pool.get()
            await self._close_connection(connection)
        
        # Close all active connections
        for connection_id in list(self._active_connections):
            connection = None
            # We don't have a way to get the connection from its ID,
            # so we can't close active connections here.
            # In a real implementation, you would keep a mapping of IDs to connections.
            if connection:
                await self._close_connection(connection)
        
        self._active_connections.clear()
        self._connection_lifetimes.clear()
    
    def get_metrics(self) -> ConnectionPoolMetrics:
        """
        Get the connection pool metrics.
        
        Returns:
            The connection pool metrics
        """
        return self.metrics
    
    @property
    def pool_size(self) -> int:
        """
        Get the current pool size.
        
        Returns:
            The current pool size
        """
        return self._pool.qsize()
    
    @property
    def active_connections(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            The number of active connections
        """
        return len(self._active_connections)


class PoolManager:
    """
    Manages multiple connection pools.
    
    This class manages multiple connection pools for different resources,
    such as databases, APIs, or services.
    """
    
    def __init__(self):
        """
        Initialize a pool manager.
        """
        self._pools = {}
        self._lock = asyncio.Lock()
        self._closed = False
        self.metrics = ConnectionPoolMetrics()
    
    async def create_pool(self,
                          name: str,
                          factory: Callable[[], Any],
                          settings: Optional[ConnectionPoolSettings] = None,
                          validate_func: Optional[Callable[[Any], bool]] = None,
                          close_func: Optional[Callable[[Any], None]] = None) -> ConnectionPool:
        """
        Create a new connection pool.
        
        Args:
            name: The name of the pool
            factory: A factory function that creates new connections
            settings: The connection pool settings
            validate_func: A function that validates connections
            close_func: A function that closes connections
            
        Returns:
            The created connection pool
        """
        if self._closed:
            raise RuntimeError("Pool manager is closed")
        
        async with self._lock:
            if name in self._pools:
                return self._pools[name]
            
            # Create a new pool
            pool = ConnectionPool(
                factory=factory,
                settings=settings,
                validate_func=validate_func,
                close_func=close_func,
                metrics=ConnectionPoolMetrics()
            )
            
            # Initialize the pool
            await pool.initialize()
            
            # Store the pool
            self._pools[name] = pool
            
            return pool
    
    async def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """
        Get a connection pool by name.
        
        Args:
            name: The name of the pool
            
        Returns:
            The connection pool, or None if not found
        """
        if name in self._pools:
            return self._pools[name]
        return None
    
    async def close_pool(self, name: str) -> None:
        """
        Close a connection pool.
        
        Args:
            name: The name of the pool
        """
        async with self._lock:
            if name in self._pools:
                pool = self._pools.pop(name)
                await pool.close()
    
    async def close_all(self) -> None:
        """
        Close all connection pools.
        """
        if self._closed:
            return
        
        self._closed = True
        
        async with self._lock:
            for name, pool in list(self._pools.items()):
                await pool.close()
            self._pools.clear()
    
    def get_metrics(self) -> Dict[str, ConnectionPoolMetrics]:
        """
        Get metrics for all connection pools.
        
        Returns:
            A dictionary mapping pool names to metrics
        """
        return {name: pool.get_metrics() for name, pool in self._pools.items()}
    
    def print_summary(self) -> None:
        """
        Print a summary of all connection pools.
        """
        print("=== Pool Manager Summary ===")
        print(f"Number of Pools: {len(self._pools)}")
        
        for name, pool in self._pools.items():
            print(f"\n--- Pool: {name} ---")
            print(f"Pool Size: {pool.pool_size}")
            print(f"Active Connections: {pool.active_connections}")
            
            metrics = pool.get_metrics()
            print(f"Total Connections: {metrics.total_connections}")
            print(f"Connection Requests: {metrics.connection_requests}")
            print(f"Pool Utilization: {metrics.pool_utilization:.2%}")
            print(f"Error Rate: {metrics.error_rate:.2%}")


class ConnectionPoolMiddleware(BaseMiddleware):
    """
    Middleware for providing connection pooling for API requests.
    
    This middleware initializes connection pools for databases and other external
    services, and provides them to API requests through the request state.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        settings: Optional[ConnectionPoolSettings] = None,
        max_connections: int = 20,
        connection_timeout: float = 5.0,
        pool_recycle: int = 300,
        pool_pre_ping: bool = True,
        **kwargs
    ):
        """
        Initialize the connection pool middleware.
        
        Args:
            database_url: The database connection URL
            redis_url: The Redis connection URL
            settings: Connection pool settings
            max_connections: Maximum number of connections in the pool
            connection_timeout: Connection timeout in seconds
            pool_recycle: Connection recycle time in seconds
            pool_pre_ping: Whether to ping connections before using them
            **kwargs: Additional options
        """
        super().__init__(**kwargs)
        self.database_url = database_url
        self.redis_url = redis_url
        self.settings = settings or ConnectionPoolSettings.create_balanced()
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.pool_manager = PoolManager(metrics_enabled=True)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the connection pools."""
        if self.initialized:
            return
        
        # Initialize database pool if URL is provided
        if self.database_url:
            try:
                await self._initialize_database_pool()
            except Exception as e:
                logger.error(f"Error initializing database pool: {e}")
        
        # Initialize Redis pool if URL is provided
        if self.redis_url:
            try:
                await self._initialize_redis_pool()
            except Exception as e:
                logger.error(f"Error initializing Redis pool: {e}")
        
        self.initialized = True
    
    async def _initialize_database_pool(self):
        """Initialize the database connection pool."""
        try:
            # Try to use SQLAlchemy if available
            try:
                import sqlalchemy
                from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
                
                # Check if the database URL is for an async driver
                is_async = any(driver in self.database_url for driver in 
                               ["postgresql+asyncpg", "mysql+aiomysql", "sqlite+aiosqlite"])
                
                if is_async:
                    engine = create_async_engine(
                        self.database_url,
                        pool_size=self.settings.min_pool_size,
                        max_overflow=self.settings.max_pool_size - self.settings.min_pool_size,
                        pool_timeout=self.connection_timeout,
                        pool_recycle=self.pool_recycle,
                        pool_pre_ping=self.pool_pre_ping
                    )
                    
                    # Create a connection pool and add it to the pool manager
                    pool = ConnectionPool(
                        name="database",
                        create_connection=lambda: engine.connect(),
                        close_connection=lambda conn: conn.close(),
                        validate_connection=lambda conn: not conn.closed,
                        min_size=self.settings.min_pool_size,
                        max_size=self.settings.max_pool_size
                    )
                else:
                    # For synchronous drivers, use a thread pool
                    engine = sqlalchemy.create_engine(
                        self.database_url,
                        pool_size=self.settings.min_pool_size,
                        max_overflow=self.settings.max_pool_size - self.settings.min_pool_size,
                        pool_timeout=self.connection_timeout,
                        pool_recycle=self.pool_recycle,
                        pool_pre_ping=self.pool_pre_ping
                    )
                    
                    # Create a connection pool and add it to the pool manager
                    pool = ConnectionPool(
                        name="database",
                        create_connection=lambda: engine.connect(),
                        close_connection=lambda conn: conn.close(),
                        validate_connection=lambda conn: not conn.closed,
                        min_size=self.settings.min_pool_size,
                        max_size=self.settings.max_pool_size
                    )
            except ImportError:
                # Fall back to a generic pool
                logger.warning("SQLAlchemy not available, using generic connection pool")
                
                # Parse the database URL to determine the database type
                db_type = self.database_url.split("://")[0] if "://" in self.database_url else "unknown"
                
                if db_type in ["postgres", "postgresql"]:
                    try:
                        import asyncpg
                        
                        async def create_pg_connection():
                            return await asyncpg.connect(self.database_url)
                        
                        async def close_pg_connection(conn):
                            await conn.close()
                        
                        pool = ConnectionPool(
                            name="database",
                            create_connection=create_pg_connection,
                            close_connection=close_pg_connection,
                            validate_connection=lambda conn: not conn.is_closed(),
                            min_size=self.settings.min_pool_size,
                            max_size=self.settings.max_pool_size
                        )
                    except ImportError:
                        logger.warning("asyncpg not available, database pooling disabled")
                        return
                elif db_type in ["mysql"]:
                    try:
                        import aiomysql
                        
                        async def create_mysql_connection():
                            return await aiomysql.connect(self.database_url)
                        
                        async def close_mysql_connection(conn):
                            conn.close()
                        
                        pool = ConnectionPool(
                            name="database",
                            create_connection=create_mysql_connection,
                            close_connection=close_mysql_connection,
                            validate_connection=lambda conn: conn.open,
                            min_size=self.settings.min_pool_size,
                            max_size=self.settings.max_pool_size
                        )
                    except ImportError:
                        logger.warning("aiomysql not available, database pooling disabled")
                        return
                else:
                    logger.warning(f"Unsupported database type: {db_type}")
                    return
            
            # Initialize the pool and add it to the pool manager
            await pool.initialize()
            self.pool_manager.add_pool(pool)
            logger.info(f"Initialized database connection pool with {self.settings.min_pool_size} connections")
        
        except Exception as e:
            logger.error(f"Error initializing database pool: {e}")
            raise
    
    async def _initialize_redis_pool(self):
        """Initialize the Redis connection pool."""
        try:
            try:
                import redis.asyncio as aioredis
                
                # Create a connection pool and add it to the pool manager
                pool = ConnectionPool(
                    name="redis",
                    create_connection=lambda: aioredis.from_url(
                        self.redis_url,
                        max_connections=self.max_connections,
                        socket_timeout=self.connection_timeout
                    ),
                    close_connection=lambda conn: conn.close(),
                    validate_connection=lambda conn: conn.ping(),
                    min_size=self.settings.min_pool_size,
                    max_size=self.settings.max_pool_size
                )
            except ImportError:
                logger.warning("aioredis not available, Redis pooling disabled")
                return
            
            # Initialize the pool and add it to the pool manager
            await pool.initialize()
            self.pool_manager.add_pool(pool)
            logger.info(f"Initialized Redis connection pool with {self.settings.min_pool_size} connections")
        
        except Exception as e:
            logger.error(f"Error initializing Redis pool: {e}")
            raise
    
    async def process_request(self, request):
        """
        Process a request (required by BaseMiddleware).
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # Make sure pools are initialized
        if not self.initialized:
            await self.initialize()
            
        # Add the pool manager to the request state
        request.state.pool_manager = self.pool_manager
            
        return request
    
    async def process_response(self, response):
        """
        Process a response (required by BaseMiddleware).
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        return response
    
    async def dispatch(
        self,
        request,
        call_next
    ):
        """
        Dispatch a request, providing connection pools.
        
        Args:
            request: The request to process
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Make sure pools are initialized
        if not self.initialized:
            await self.initialize()
        
        # Add the pool manager to the request state
        request.state.pool_manager = self.pool_manager
        
        # Process the request
        response = await call_next(request)
        
        return response
    
    async def shutdown(self):
        """Shutdown all connection pools."""
        await self.pool_manager.close_all_pools()
        self.initialized = False
        logger.info("Connection pools shut down")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get connection pool metrics.
        
        Returns:
            A dictionary of metrics
        """
        return self.pool_manager.get_metrics()
    
    def print_metrics(self):
        """Print connection pool metrics."""
        self.pool_manager.print_metrics() 