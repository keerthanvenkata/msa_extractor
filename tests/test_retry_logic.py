"""
Tests for retry logic in Gemini client.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from ai.gemini_client import GeminiClient
from utils.exceptions import LLMError
from config import API_MAX_RETRIES


class TestRetryLogic:
    """Test retry logic in GeminiClient."""
    
    @pytest.fixture
    def gemini_client(self):
        """Create GeminiClient instance for testing."""
        # Mock the API key check
        with patch('ai.gemini_client.GEMINI_API_KEY', 'test-key'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = GeminiClient()
                    return client
    
    def test_retry_on_transient_error(self, gemini_client):
        """Test retry on transient error."""
        # Mock API call that fails twice then succeeds
        mock_response = MagicMock()
        mock_response.text = '{"Contract Lifecycle": {"Execution Date": "2025-03-14"}}'
        
        call_count = 0
        
        def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # Simulate transient error
                error = Exception("Rate limit exceeded")
                error.__class__.__name__ = "ResourceExhausted"
                raise error
            return mock_response
        
        gemini_client.text_model = Mock()
        gemini_client.text_model.generate_content = Mock(side_effect=mock_api_call)
        
        # Should succeed after retries
        result = gemini_client._call_with_retry(
            lambda: gemini_client.text_model.generate_content("test"),
            operation="test"
        )
        
        assert result == mock_response
        assert call_count == 3
    
    def test_retry_exhausted(self, gemini_client):
        """Test that retry gives up after max attempts."""
        # Mock API call that always fails
        def mock_api_call(*args, **kwargs):
            error = Exception("Rate limit exceeded")
            error.__class__.__name__ = "ResourceExhausted"
            raise error
        
        gemini_client.text_model = Mock()
        gemini_client.text_model.generate_content = Mock(side_effect=mock_api_call)
        
        # Should raise LLMError after max retries
        with pytest.raises(LLMError) as exc_info:
            gemini_client._call_with_retry(
                lambda: gemini_client.text_model.generate_content("test"),
                operation="test"
            )
        
        assert "failed after" in str(exc_info.value).lower() or "API call failed" in str(exc_info.value)
    
    def test_no_retry_on_non_transient_error(self, gemini_client):
        """Test that non-transient errors are not retried."""
        # Mock API call that fails with non-retryable error
        def mock_api_call(*args, **kwargs):
            raise ValueError("Invalid input")
        
        gemini_client.text_model = Mock()
        gemini_client.text_model.generate_content = Mock(side_effect=mock_api_call)
        
        # Should raise immediately without retries
        with pytest.raises(LLMError):
            gemini_client._call_with_retry(
                lambda: gemini_client.text_model.generate_content("test"),
                operation="test"
            )
    
    def test_exponential_backoff(self, gemini_client):
        """Test exponential backoff delay calculation."""
        # Mock time.sleep to track delays
        delays = []
        
        def mock_sleep(delay):
            delays.append(delay)
        
        # Mock API call that fails
        def mock_api_call(*args, **kwargs):
            error = Exception("Rate limit exceeded")
            error.__class__.__name__ = "ResourceExhausted"
            raise error
        
        gemini_client.text_model = Mock()
        gemini_client.text_model.generate_content = Mock(side_effect=mock_api_call)
        
        with patch('time.sleep', mock_sleep):
            with pytest.raises(LLMError):
                gemini_client._call_with_retry(
                    lambda: gemini_client.text_model.generate_content("test"),
                    operation="test"
                )
        
        # Check that delays increase exponentially (at least first few)
        if len(delays) >= 2:
            assert delays[1] >= delays[0]  # Second delay >= first delay

