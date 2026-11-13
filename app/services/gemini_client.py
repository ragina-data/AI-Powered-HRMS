
"""
Gemini Client
=============

Purpose:
    Provide a centralized integration with Google's Gemini API.

Responsibilities:
    1. Initialize the Google Gen AI SDK.
    2. Send prompts to Gemini.
    3. Apply system instructions and generation settings.
    4. Extract generated response text.
    5. Capture token usage.
    6. Handle API errors safely.

Architecture:
    This client is independent of PostgreSQL and FastAPI.

    The AI Assistant Service will call this client.
"""

import logging

from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from app.core.config import settings


logger = logging.getLogger(__name__)


# ============================================================
# DEFAULT ASSISTANT INSTRUCTIONS
# ============================================================

DEFAULT_SYSTEM_INSTRUCTION = """
You are the AI Virtual Assistant for an organization's HRMS.

Your responsibilities:

1. Communicate professionally and clearly.
2. Help employees understand HR-related questions.
3. Provide accurate and concise responses.
4. Do not invent employee information, leave balances,
   document statuses, or company policies.
5. Do not claim to have retrieved database information
   unless the backend has actually provided it.
6. When verified HR information is unavailable, clearly
   explain that it cannot currently be confirmed.
7. Never request passwords, JWT tokens, or API credentials.

Respond in a helpful and professional manner.
"""


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class GeminiClientError(Exception):
    """Base exception for Gemini client operations."""


class GeminiConfigurationError(GeminiClientError):
    """Raised when Gemini configuration is incomplete."""


class GeminiGenerationError(GeminiClientError):
    """Raised when Gemini response generation fails."""


class GeminiEmptyResponseError(GeminiGenerationError):
    """Raised when Gemini returns no usable text."""


# ============================================================
# GEMINI RESPONSE DATA STRUCTURE
# ============================================================

@dataclass(frozen=True)
class GeminiGenerationResult:
    """
    Structured result returned by the Gemini client.

    Attributes:
        text:
            Generated assistant response.

        model_name:
            Gemini model version or configured model name.

        prompt_token_count:
            Number of input tokens.

        response_token_count:
            Number of generated candidate tokens.

        total_token_count:
            Total token usage reported by Gemini.
    """

    text: str
    model_name: str
    prompt_token_count: int | None
    response_token_count: int | None
    total_token_count: int | None


# ============================================================
# GEMINI CLIENT
# ============================================================

class GeminiClient:
    """
    Centralized Gemini API client.

    The client uses configuration from app.core.config.Settings.

    Example:

        gemini = GeminiClient()

        result = gemini.generate_response(
            prompt="What is annual leave?"
        )

        print(result.text)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ):

        resolved_api_key = (
            api_key or settings.GEMINI_API_KEY
        ).strip()

        resolved_model_name = (
            model_name or settings.GEMINI_MODEL
        ).strip()

        # Validate API credentials.

        if not resolved_api_key:
            raise GeminiConfigurationError(
                "Gemini API key is not configured."
            )

        if not resolved_model_name:
            raise GeminiConfigurationError(
                "Gemini model name is not configured."
            )

        self.model_name = resolved_model_name

        # Initialize the Google Gen AI SDK client.

        try:
            self._client = genai.Client(
                api_key=resolved_api_key,
            )

        except Exception as exc:

            logger.error(
                "Gemini client initialization failed. "
                "Error type: %s",
                type(exc).__name__,
            )

            raise GeminiConfigurationError(
                "Unable to initialize Gemini client."
            ) from exc

    # ========================================================
    # GENERATE RESPONSE
    # ========================================================

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> GeminiGenerationResult:
        """
        Generate an AI response using Gemini.

        Args:
            prompt:
                Employee question or conversation prompt.

            system_instruction:
                Instructions controlling assistant behavior.

            temperature:
                Controls response randomness.

            max_output_tokens:
                Maximum generated output tokens.

        Returns:
            GeminiGenerationResult containing response text,
            model information and token usage.
        """

        # ----------------------------------------------------
        # INPUT VALIDATION
        # ----------------------------------------------------

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        if not 0 <= temperature <= 2:
            raise ValueError(
                "Temperature must be between 0 and 2."
            )

        if max_output_tokens <= 0:
            raise ValueError(
                "Maximum output tokens must be positive."
            )

        prompt = prompt.strip()

        # ----------------------------------------------------
        # GENERATION CONFIGURATION
        # ----------------------------------------------------

        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            candidate_count=1,
        )

        # ----------------------------------------------------
        # CALL GEMINI API
        # ----------------------------------------------------

        try:

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=generation_config,
            )

        except errors.APIError as exc:

            logger.error(
                "Gemini API error. HTTP status: %s",
                exc.code,
            )

            raise GeminiGenerationError(
                f"Gemini API request failed (HTTP {exc.code})."
            ) from exc

        except Exception as exc:

            logger.error(
                "Gemini generation failed. Error type: %s",
                type(exc).__name__,
            )

            raise GeminiGenerationError(
                "Unable to generate a response from Gemini."
            ) from exc

        # ----------------------------------------------------
        # EXTRACT GENERATED TEXT
        # ----------------------------------------------------

        generated_text = response.text

        if not generated_text or not generated_text.strip():

            logger.warning(
                "Gemini returned an empty text response."
            )

            raise GeminiEmptyResponseError(
                "Gemini did not return a usable text response."
            )

        generated_text = generated_text.strip()

        # ----------------------------------------------------
        # EXTRACT TOKEN USAGE
        # ----------------------------------------------------

        usage = response.usage_metadata

        prompt_tokens = (
            usage.prompt_token_count
            if usage is not None
            else None
        )

        response_tokens = (
            usage.candidates_token_count
            if usage is not None
            else None
        )

        total_tokens = (
            usage.total_token_count
            if usage is not None
            else None
        )

        # ----------------------------------------------------
        # EXTRACT MODEL INFORMATION
        # ----------------------------------------------------

        actual_model_name = (
            getattr(response, "model_version", None)
            or self.model_name
        )

        # ----------------------------------------------------
        # RETURN STRUCTURED RESPONSE
        # ----------------------------------------------------

        return GeminiGenerationResult(
            text=generated_text,
            model_name=actual_model_name,
            prompt_token_count=prompt_tokens,
            response_token_count=response_tokens,
            total_token_count=total_tokens,
        )

    # ========================================================
    # CLOSE CLIENT
    # ========================================================

    def close(self) -> None:
        """
        Close the underlying HTTP client when no longer needed.
        """

        self._client.close()
