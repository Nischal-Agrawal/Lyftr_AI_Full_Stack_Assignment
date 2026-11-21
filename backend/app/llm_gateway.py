import time
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
import litellm
from litellm.caching import Cache
from litellm.exceptions import (
    RateLimitError,
    AuthenticationError,
    PermissionDeniedError,
    BadRequestError,
    InternalServerError,
    BadGatewayError,
    ServiceUnavailableError,
    APIConnectionError,
    APIError,
    BudgetExceededError,
)
from app.config import settings, KeyConfig

logger = logging.getLogger("llm_gateway")
logging.basicConfig(level=logging.INFO)

litellm.suppress_debug_info = True

# Initialize LiteLLM Built-in Cache
try:
    if settings.LITELLM_CACHE_TYPE == "disk":
        litellm.cache = Cache(type="disk", disk_cache_dir="/data/litellm_cache")
    else:
        litellm.cache = Cache(type="local")
except Exception as e:
    logger.warning(f"Failed to initialize LiteLLM cache with type {settings.LITELLM_CACHE_TYPE}: {e}")
    litellm.cache = Cache(type="local")


class AllProvidersUnavailableException(Exception):
    """Raised when all configured LLM providers/keys fail."""
    def __init__(self, message: str = "all providers unavailable"):
        super().__init__(message)
        self.message = message


def get_exact_cache_key(model: str, messages: List[Dict[str, str]]) -> str:
    """
    Computes a deterministic hash over model + full message list.
    Guarantees cross-session cache hits regardless of API key or session ID.
    """
    serialized = json.dumps({"model": model, "messages": messages}, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def parse_simulate_failure_header(header_val: Optional[str]) -> Dict[str, int]:
    """
    Parses comma-separated <key_id>=<status> pairs, e.g. 'key_1=429,key_2=500' or '*=429'.
    Honored ONLY when settings.ENABLE_FAILURE_SIMULATION is True.
    """
    if not header_val or not settings.ENABLE_FAILURE_SIMULATION:
        return {}
    
    simulations: Dict[str, int] = {}
    parts = header_val.split(",")
    for part in parts:
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            try:
                simulations[k] = int(v)
            except ValueError:
                continue
    return simulations


def calculate_tokens(model: str, messages: List[Dict[str, str]], reply: str, response: Any) -> Tuple[int, int]:
    """
    Extracts or calculates per-request prompt and completion tokens.
    Guarantees positive integer counts.
    """
    input_tokens = 0
    output_tokens = 0

    usage = getattr(response, "usage", None)
    if usage:
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
    elif isinstance(response, dict) and "usage" in response:
        usage_dict = response["usage"]
        input_tokens = usage_dict.get("prompt_tokens", 0) or 0
        output_tokens = usage_dict.get("completion_tokens", 0) or 0

    if not input_tokens or input_tokens <= 0:
        try:
            input_tokens = litellm.token_counter(model=model, messages=messages)
        except Exception:
            total_chars = sum(len(m.get("content", "")) for m in messages)
            input_tokens = max(1, total_chars // 4)

    if not output_tokens or output_tokens <= 0:
        try:
            output_tokens = litellm.token_counter(model=model, text=reply)
        except Exception:
            output_tokens = max(1, len(reply) // 4)

    return max(1, int(input_tokens)), max(1, int(output_tokens))


async def generate_chat_turn(
    messages: List[Dict[str, str]],
    simulate_failure_header: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Executes a multi-turn LLM chat turn through LiteLLM with:
    1. Built-in caching (bypassed if simulating failure)
    2. Deterministic sequential key failover (key_1 -> key_2 -> ...)
    3. Failure simulation hook (X-Simulate-Failure)
    4. Accurate per-request token and latency accounting
    """
    start_time = time.perf_counter()
    simulated_failures = parse_simulate_failure_header(simulate_failure_header)
    is_simulating_failure = bool(simulated_failures)

    key_pool = settings.key_pool
    if not key_pool:
        raise AllProvidersUnavailableException("all providers unavailable")

    primary_model = key_pool[0].model

    # Check LiteLLM Built-in Cache directly if failure simulation is not active
    if not is_simulating_failure and litellm.cache is not None:
        try:
            cache_key = get_exact_cache_key(model=primary_model, messages=messages)
            cached_data = None
            if hasattr(litellm.cache, "cache") and hasattr(litellm.cache.cache, "get_cache"):
                cached_data = litellm.cache.cache.get_cache(cache_key)
            if cached_data is not None:
                # Cache hit!
                reply = cached_data.get("reply", "")
                if reply:
                    input_tokens = cached_data.get("input_tokens", 1)
                    output_tokens = cached_data.get("output_tokens", 1)
                    latency_ms = max(1, int(round((time.perf_counter() - start_time) * 1000)))
                    metadata = {
                        "resolution_source": "LLM_CACHE",
                        "model": primary_model,
                        "latency_ms": latency_ms,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "key_id": None,
                        "fallback_attempts": 0,
                    }
                    return reply, metadata
        except Exception as e:
            logger.debug(f"LiteLLM cache pre-lookup error: {e}")

    fallback_attempts = 0

    for key_cfg in key_pool:
        key_id = key_cfg.key_id
        model = key_cfg.model
        api_key = key_cfg.api_key

        # Check for simulated failure on this key or wildcard '*'
        simulated_status = None
        if key_id in simulated_failures:
            simulated_status = simulated_failures[key_id]
        elif "*" in simulated_failures:
            simulated_status = simulated_failures["*"]

        if simulated_status is not None:
            logger.info(
                f'{{"event": "key_failure_simulated", "key_id": "{key_id}", "status_code": {simulated_status}}}'
            )
            fallback_attempts += 1
            continue

        try:
            # Support automatic mock responses if mock/test keys are used without real credentials
            call_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "api_key": api_key,
                "timeout": settings.LLM_TIMEOUT_SECONDS,
                "num_retries": 0,
                "caching": not is_simulating_failure,
            }
            if is_simulating_failure:
                call_kwargs["cache"] = {"no-cache": True}

            if api_key.startswith("mock-") or api_key.startswith("test-"):
                user_msg = messages[-1].get("content", "") if messages else "Hello"
                call_kwargs["mock_response"] = f"Response to: {user_msg}"

            response = await litellm.acompletion(**call_kwargs)

            # Extract reply text
            reply_text = ""
            choices = getattr(response, "choices", [])
            if choices and len(choices) > 0:
                first_choice = choices[0]
                message_obj = getattr(first_choice, "message", None)
                if message_obj:
                    reply_text = getattr(message_obj, "content", "") or ""
                elif isinstance(first_choice, dict):
                    reply_text = first_choice.get("message", {}).get("content", "")

            reply_text = reply_text.strip()
            if not reply_text:
                logger.warning(f"Key {key_id} returned empty reply, failing over...")
                fallback_attempts += 1
                continue

            # Detect LiteLLM cache hit
            hidden_params = getattr(response, "_hidden_params", {}) or {}
            is_cache_hit = bool(hidden_params.get("cache_hit", False)) and not is_simulating_failure

            latency_ms = max(1, int(round((time.perf_counter() - start_time) * 1000)))
            input_tokens, output_tokens = calculate_tokens(model, messages, reply_text, response)

            # Populate LiteLLM built-in cache for subsequent turns/sessions if not simulating
            if not is_simulating_failure and litellm.cache is not None:
                try:
                    c_key = get_exact_cache_key(model=model, messages=messages)
                    payload = {
                        "reply": reply_text,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "model": model,
                    }
                    if hasattr(litellm.cache, "cache") and hasattr(litellm.cache.cache, "set_cache"):
                        litellm.cache.cache.set_cache(c_key, payload)
                except Exception as ce:
                    logger.debug(f"Error updating litellm cache: {ce}")

            if is_cache_hit:
                metadata = {
                    "resolution_source": "LLM_CACHE",
                    "model": model,
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "key_id": None,
                    "fallback_attempts": 0,
                }
            else:
                metadata = {
                    "resolution_source": "LIVE_INFERENCE",
                    "model": model,
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "key_id": key_id,
                    "fallback_attempts": fallback_attempts,
                }

            return reply_text, metadata

        except (
            RateLimitError,
            AuthenticationError,
            PermissionDeniedError,
            BadRequestError,
            InternalServerError,
            BadGatewayError,
            ServiceUnavailableError,
            APIConnectionError,
            APIError,
            BudgetExceededError,
            TimeoutError,
            Exception,
        ) as err:
            logger.warning(
                f'{{"event": "provider_error", "key_id": "{key_id}", "error_type": "{type(err).__name__}", "error": "{err}"}}'
            )
            fallback_attempts += 1
            continue

    # If all keys in pool were exhausted without success
    raise AllProvidersUnavailableException("all providers unavailable")
