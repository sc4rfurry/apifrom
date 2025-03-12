"""
Tests for the Subresource Integrity middleware using async/await syntax.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.sri import (
    SRIMiddleware,
    SRIPolicy,
    SRIGenerator,
    SRIHashAlgorithm,
    SRIBuilder,
)
from tests.middleware_test_helper import AsyncMiddlewareTester, MockRequest, MockResponse


class TestSRIHashAlgorithmAsync:
    """
    Tests for the SRIHashAlgorithm enum using async/await syntax.
    """
    
    def test_algorithms(self):
        """
        Test that algorithms are defined correctly.
        """
        assert SRIHashAlgorithm.SHA256.value == "sha256"
        assert SRIHashAlgorithm.SHA384.value == "sha384"
        assert SRIHashAlgorithm.SHA512.value == "sha512"


class TestSRIGeneratorAsync:
    """
    Tests for the SRIGenerator class using async/await syntax.
    """
    
    def test_generate_hash(self):
        """
        Test that hash generation works.
        """
        content = "Test content"
        
        # Test SHA256
        hash_sha256 = SRIGenerator.generate_hash(content, SRIHashAlgorithm.SHA256)
        assert hash_sha256.startswith("sha256-")
        
        # Test SHA384
        hash_sha384 = SRIGenerator.generate_hash(content, SRIHashAlgorithm.SHA384)
        assert hash_sha384.startswith("sha384-")
        
        # Test SHA512
        hash_sha512 = SRIGenerator.generate_hash(content, SRIHashAlgorithm.SHA512)
        assert hash_sha512.startswith("sha512-")
    
    def test_generate_integrity_attribute(self):
        """
        Test that integrity attribute generation works.
        """
        content = "Test content"
        
        # Test single algorithm
        integrity = SRIGenerator.generate_integrity_attribute(content, [SRIHashAlgorithm.SHA256])
        assert integrity.startswith("sha256-")
        
        # Test multiple algorithms
        integrity = SRIGenerator.generate_integrity_attribute(
            content, [SRIHashAlgorithm.SHA256, SRIHashAlgorithm.SHA384]
        )
        assert " " in integrity
        assert integrity.split(" ")[0].startswith("sha256-")
        assert integrity.split(" ")[1].startswith("sha384-")
    
    def test_verify_integrity(self):
        """
        Test that integrity verification works.
        """
        content = "Test content"
        
        # Generate integrity attribute
        integrity = SRIGenerator.generate_integrity_attribute(content, [SRIHashAlgorithm.SHA256])
        
        # Verify with correct content
        assert SRIGenerator.verify_integrity(content, integrity)
        
        # Verify with incorrect content
        assert not SRIGenerator.verify_integrity("Wrong content", integrity)


class TestSRIMiddlewareAsync:
    """
    Tests for the SRIMiddleware class using async/await syntax.
    """
    
    @pytest.fixture
    def script_sources(self):
        """Fixture for script sources"""
        return {
            "https://example.com/script.js": "sha384-test-hash"
        }
    
    @pytest.fixture
    def style_sources(self):
        """Fixture for style sources"""
        return {
            "https://example.com/style.css": "sha384-test-hash"
        }
    
    @pytest.fixture
    def sri_middleware(self, script_sources, style_sources):
        """Fixture for SRI middleware"""
        return SRIMiddleware(
            script_sources=script_sources,
            style_sources=style_sources,
            exempt_paths=["/exempt"]
        )
    
    @pytest.fixture
    def html_response(self):
        """Fixture for HTML response"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://example.com/script.js"></script>
            <link rel="stylesheet" href="https://example.com/style.css">
        </head>
        <body>
            <h1>Test</h1>
        </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_process_request(self, sri_middleware, html_response):
        """
        Test that the middleware processes requests correctly.
        """
        # Create a mock request and response
        request = MockRequest(path="/")
        response = MockResponse(
            body=html_response,
            headers={"Content-Type": "text/html"}
        )
        response.request = request
        
        # Process the response
        processed_response = await sri_middleware.process_response(response)
        
        # Check that integrity attributes were added
        assert 'integrity="sha384-test-hash"' in processed_response.body
    
    @pytest.mark.asyncio
    async def test_exempt_path(self, sri_middleware, html_response):
        """
        Test that exempt paths are not processed.
        """
        # Create a mock request and response
        request = MockRequest(path="/exempt")
        response = MockResponse(
            body=html_response,
            headers={"Content-Type": "text/html"}
        )
        response.request = request
        
        # Process the response
        processed_response = await sri_middleware.process_response(response)
        
        # Check that integrity attributes were not added
        assert 'integrity="sha384-test-hash"' not in processed_response.body
    
    @pytest.mark.asyncio
    async def test_non_html_response(self, sri_middleware):
        """
        Test that non-HTML responses are not processed.
        """
        # Create a mock request and response
        request = MockRequest(path="/")
        response = MockResponse(
            body='{"key": "value"}',
            headers={"Content-Type": "application/json"}
        )
        response.request = request
        
        # Process the response
        processed_response = await sri_middleware.process_response(response)
        
        # Check that the response was not modified
        assert processed_response.body == '{"key": "value"}'
    
    def test_add_integrity_to_html(self, sri_middleware, html_response):
        """
        Test that integrity attributes are added to HTML.
        """
        # Add integrity attributes to HTML
        processed_html = sri_middleware._add_integrity_to_html(html_response)
        
        # Check that integrity attributes were added
        assert 'integrity="sha384-test-hash"' in processed_html


class TestSRIPolicyAsync:
    """
    Tests for the SRIPolicy class using async/await syntax.
    """
    
    def test_add_script_source(self):
        """
        Test that script sources can be added.
        """
        policy = SRIPolicy()
        policy.add_script_source("https://example.com/script.js", "sha384-test-hash")
        
        assert "https://example.com/script.js" in policy.script_sources
        assert policy.script_sources["https://example.com/script.js"] == "sha384-test-hash"
    
    def test_add_style_source(self):
        """
        Test that style sources can be added.
        """
        policy = SRIPolicy()
        policy.add_style_source("https://example.com/style.css", "sha384-test-hash")
        
        assert "https://example.com/style.css" in policy.style_sources
        assert policy.style_sources["https://example.com/style.css"] == "sha384-test-hash"
    
    def test_set_algorithms(self):
        """
        Test that algorithms can be set.
        """
        policy = SRIPolicy()
        policy.set_algorithms([SRIHashAlgorithm.SHA256, SRIHashAlgorithm.SHA512])
        
        assert policy.algorithms == [SRIHashAlgorithm.SHA256, SRIHashAlgorithm.SHA512]
    
    def test_enable_verification(self):
        """
        Test that verification can be enabled.
        """
        policy = SRIPolicy()
        policy.enable_verification(True)
        
        assert policy.verify_external_resources is True
    
    @pytest.mark.asyncio
    async def test_compute_missing_integrity_values(self):
        """
        Test that missing integrity values are computed.
        """
        # Create a policy
        policy = SRIPolicy()
        policy.add_script_source("https://example.com/script.js", None)
        
        # Mock the compute_integrity function
        async def mock_compute_integrity(url):
            return "sha384-mocked-hash"
        
        # Patch the _compute_integrity method
        with patch.object(policy, '_compute_integrity', side_effect=mock_compute_integrity):
            # Compute missing integrity values
            await policy.compute_missing_integrity_values()
            
            # Check that the integrity value was computed
            assert policy.script_sources["https://example.com/script.js"] == "sha384-mocked-hash"


class TestSRIBuilderAsync:
    """
    Tests for the SRIBuilder class using async/await syntax.
    """
    
    def test_create_empty_policy(self):
        """
        Test that an empty policy can be created.
        """
        policy = SRIBuilder.create_empty_policy()
        
        assert isinstance(policy, SRIPolicy)
        assert len(policy.script_sources) == 0
        assert len(policy.style_sources) == 0
    
    def test_create_common_cdn_policy(self):
        """
        Test that a common CDN policy can be created.
        """
        policy = SRIBuilder.create_common_cdn_policy()
        
        assert isinstance(policy, SRIPolicy)
        assert len(policy.script_sources) > 0
        assert len(policy.style_sources) > 0
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_create_policy_from_html(self, mock_session):
        """
        Test that a policy can be created from HTML.
        """
        # Mock the session and response
        mock_response = MagicMock()
        mock_response.text = AsyncMock(return_value="script content")
        
        # Create a context manager mock for the response
        response_context = MagicMock()
        response_context.__aenter__ = AsyncMock(return_value=mock_response)
        response_context.__aexit__ = AsyncMock(return_value=None)
        
        # Create a context manager mock for the session
        session_context = MagicMock()
        session_context.__aenter__ = AsyncMock(return_value=session_context)
        session_context.__aexit__ = AsyncMock(return_value=None)
        session_context.get = MagicMock(return_value=response_context)
        
        # Set up the mock_session to return our session_context
        mock_session.return_value = session_context
        
        # Create HTML with script and style tags
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://example.com/script.js"></script>
            <link rel="stylesheet" href="https://example.com/style.css">
        </head>
        <body>
            <h1>Test</h1>
        </body>
        </html>
        """
        
        # Create a policy from HTML
        with patch('apifrom.security.sri.SRIGenerator.generate_hash', return_value='sha256-mockhash'):
            policy = await SRIBuilder.create_policy_from_html(html)
            
        # Assert that the policy contains the expected sources
        assert 'https://example.com/script.js' in policy.script_sources
        assert 'https://example.com/style.css' in policy.style_sources 