#!/usr/bin/env python3
"""
Lyftr AI Full-Stack Assignment: Automated Live Contract Verification Script

Tests every required endpoint, contract constraint, cache hit behavior,
deterministic key failover, and validation rules against a live running backend.
Usage:
    python scripts/verify_contract.py [--base-url http://localhost:8000]
"""

import sys
import time
import uuid
import argparse
import urllib.request
import urllib.error
import json
from typing import Dict, Any, Tuple, Optional

# Color terminal formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner(base_url: str):
    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}{CYAN}  Lyftr AI Full-Stack Assignment: Automated Contract Verifier  {RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}")
    print(f"Target Base URL: {YELLOW}{base_url}{RESET}\n")


def make_request(
    url: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Any]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status_code = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return status_code, parsed
    except urllib.error.HTTPError as err:
        content = err.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content
        return err.code, parsed
    except Exception as exc:
        return 0, str(exc)


class ContractVerifier:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.passed = 0
        self.failed = 0

    def assert_check(self, title: str, condition: bool, error_msg: str = ""):
        if condition:
            self.passed += 1
            print(f"  [{GREEN}PASS{RESET}] {title}")
        else:
            self.failed += 1
            print(f"  [{RED}FAIL{RESET}] {title} — {error_msg}")

    def run_all(self) -> bool:
        print(f"{BOLD}Phase 1: Health Check (GET /health){RESET}")
        self.verify_health()

        print(f"\n{BOLD}Phase 2: Live Inference Happy Path (POST /chat){RESET}")
        live_meta, live_reply = self.verify_live_inference()

        print(f"\n{BOLD}Phase 3: Cross-Session Response Caching (POST /chat){RESET}")
        self.verify_caching(live_meta, live_reply)

        print(f"\n{BOLD}Phase 4: Multi-Turn Conversation & History (GET /sessions/{{id}}/messages){RESET}")
        self.verify_multi_turn()

        print(f"\n{BOLD}Phase 5: Key Failover via X-Simulate-Failure (POST /chat){RESET}")
        self.verify_failover()

        print(f"\n{BOLD}Phase 6: Strict Input Validation (HTTP 422) & 404 Contract{RESET}")
        self.verify_validation_and_errors()

        self.print_summary()
        return self.failed == 0

    def verify_health(self):
        status, data = make_request(f"{self.base_url}/health")
        self.assert_check("Health endpoint returns HTTP 200", status == 200, f"Got {status}: {data}")
        if isinstance(data, dict):
            self.assert_check("status == 'ok'", data.get("status") == "ok")
            self.assert_check("keys_configured >= 2", data.get("keys_configured", 0) >= 2)
            self.assert_check("cache_enabled is True", data.get("cache_enabled") is True)
        else:
            self.assert_check("Health response is JSON", False, str(data))

    def verify_live_inference(self) -> Tuple[Optional[Dict[str, Any]], str]:
        session_id = f"test-live-{uuid.uuid4().hex[:8]}"
        prompt = "Explain why API key failover is critical in production in one sentence."

        status, data = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_id, "message": prompt},
        )

        self.assert_check("POST /chat returns HTTP 200", status == 200, f"Got {status}: {data}")
        if not isinstance(data, dict):
            return None, ""

        self.assert_check("Echoes exact session_id", data.get("session_id") == session_id)
        reply = data.get("reply", "")
        self.assert_check("Reply is non-empty string", isinstance(reply, str) and len(reply) > 0)

        meta = data.get("metadata", {})
        self.assert_check(
            "resolution_source == 'LIVE_INFERENCE'",
            meta.get("resolution_source") == "LIVE_INFERENCE",
            f"Got {meta.get('resolution_source')}",
        )
        self.assert_check("key_id == 'key_1'", meta.get("key_id") == "key_1", f"Got {meta.get('key_id')}")
        self.assert_check("fallback_attempts == 0", meta.get("fallback_attempts") == 0)
        self.assert_check(
            "input_tokens and output_tokens are positive integers",
            isinstance(meta.get("input_tokens"), int) and meta.get("input_tokens", 0) > 0 and
            isinstance(meta.get("output_tokens"), int) and meta.get("output_tokens", 0) > 0,
        )
        self.assert_check(
            "latency_ms is positive integer",
            isinstance(meta.get("latency_ms"), int) and meta.get("latency_ms", 0) > 0,
        )

        return meta, reply

    def verify_caching(self, prior_meta: Optional[Dict[str, Any]], prior_reply: str):
        # Session B: Brand new session, exact same prompt
        session_b = f"test-cache-{uuid.uuid4().hex[:8]}"
        prompt = "Explain why API key failover is critical in production in one sentence."

        status, data = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_b, "message": prompt},
        )

        self.assert_check("Cache hit test returns HTTP 200", status == 200, f"Got {status}: {data}")
        if isinstance(data, dict):
            meta = data.get("metadata", {})
            self.assert_check(
                "resolution_source == 'LLM_CACHE'",
                meta.get("resolution_source") == "LLM_CACHE",
                f"Got {meta.get('resolution_source')}",
            )
            self.assert_check("key_id is null on LLM_CACHE", meta.get("key_id") is None)
            self.assert_check("fallback_attempts == 0 on LLM_CACHE", meta.get("fallback_attempts") == 0)
            if prior_reply:
                self.assert_check("Cache hit returns identical reply text", data.get("reply") == prior_reply)
            if prior_meta:
                self.assert_check(
                    "Cached input_tokens and output_tokens match original turn",
                    meta.get("input_tokens") == prior_meta.get("input_tokens") and
                    meta.get("output_tokens") == prior_meta.get("output_tokens"),
                )

        # Different prompt should be cache miss
        session_c = f"test-diff-{uuid.uuid4().hex[:8]}"
        status_c, data_c = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_c, "message": "What is 7 multiplied by 8?"},
        )
        if isinstance(data_c, dict):
            self.assert_check(
                "Different prompt results in resolution_source == 'LIVE_INFERENCE'",
                data_c.get("metadata", {}).get("resolution_source") == "LIVE_INFERENCE",
            )

    def verify_multi_turn(self):
        session_id = f"test-multi-{uuid.uuid4().hex[:8]}"

        # Turn 1
        s1, _ = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_id, "message": "My favorite color is emerald green."},
        )
        self.assert_check("Turn 1 succeeds", s1 == 200)

        # Turn 2
        s2, d2 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_id, "message": "What is my favorite color?"},
        )
        self.assert_check("Turn 2 succeeds", s2 == 200)

        # Retrieve history
        status, data = make_request(f"{self.base_url}/sessions/{session_id}/messages")
        self.assert_check("GET /sessions/{id}/messages returns HTTP 200", status == 200)
        if isinstance(data, dict):
            messages = data.get("messages", [])
            self.assert_check("Session history contains exactly 4 messages", len(messages) == 4)
            if len(messages) == 4:
                self.assert_check(
                    "Messages in chronological order without system prompt",
                    messages[0].get("role") == "user" and
                    messages[1].get("role") == "assistant" and
                    messages[2].get("role") == "user" and
                    messages[3].get("role") == "assistant",
                )

    def verify_failover(self):
        # 1. key_1=429 -> should fail over to key_2 with fallback_attempts=1
        session_1 = f"test-fail-429-{uuid.uuid4().hex[:8]}"
        status1, data1 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_1, "message": "Testing failover on 429"},
            headers={"X-Simulate-Failure": "key_1=429"},
        )
        self.assert_check("X-Simulate-Failure: key_1=429 returns HTTP 200", status1 == 200)
        if isinstance(data1, dict):
            meta1 = data1.get("metadata", {})
            self.assert_check("Fails over to key_2 on 429", meta1.get("key_id") == "key_2")
            self.assert_check("fallback_attempts == 1", meta1.get("fallback_attempts") == 1)
            self.assert_check("resolution_source == 'LIVE_INFERENCE'", meta1.get("resolution_source") == "LIVE_INFERENCE")

        # 2. key_1=500 -> should fail over to key_2
        session_2 = f"test-fail-500-{uuid.uuid4().hex[:8]}"
        status2, data2 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_2, "message": "Testing failover on 500"},
            headers={"X-Simulate-Failure": "key_1=500"},
        )
        self.assert_check("X-Simulate-Failure: key_1=500 returns HTTP 200", status2 == 200)
        if isinstance(data2, dict):
            meta2 = data2.get("metadata", {})
            self.assert_check("Fails over to key_2 on 500", meta2.get("key_id") == "key_2")
            self.assert_check("fallback_attempts == 1 on 500", meta2.get("fallback_attempts") == 1)

        # 3. *=429 -> all keys down -> 503 {"detail": "all providers unavailable"}
        session_3 = f"test-fail-all-{uuid.uuid4().hex[:8]}"
        status3, data3 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_3, "message": "Testing all keys down"},
            headers={"X-Simulate-Failure": "*=429"},
        )
        self.assert_check("X-Simulate-Failure: *=429 returns HTTP 503", status3 == 503)
        self.assert_check(
            "Returns exact detail: 'all providers unavailable'",
            isinstance(data3, dict) and data3.get("detail") == "all providers unavailable",
        )

        # Ensure failed 503 turn wrote NOTHING to database
        status_check, _ = make_request(f"{self.base_url}/sessions/{session_3}/messages")
        self.assert_check("503 failure persists nothing to SQLite (returns 404)", status_check == 404)

        # 4. Request-scoped isolation: next request without header succeeds on key_1
        session_4 = f"test-isolated-{uuid.uuid4().hex[:8]}"
        status4, data4 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": session_4, "message": "Testing isolation after failure"},
        )
        self.assert_check("Subsequent request without header succeeds", status4 == 200)
        if isinstance(data4, dict):
            meta4 = data4.get("metadata", {})
            self.assert_check("Isolated request succeeds on key_1", meta4.get("key_id") == "key_1")
            self.assert_check("fallback_attempts == 0 on normal request", meta4.get("fallback_attempts") == 0)

    def verify_validation_and_errors(self):
        # Empty message
        s1, d1 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": "val-1", "message": ""},
        )
        self.assert_check("Empty message returns HTTP 422", s1 == 422)

        # Whitespace-only message
        s2, d2 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": "val-2", "message": "     "},
        )
        self.assert_check("Whitespace-only message returns HTTP 422", s2 == 422)

        # Exceeding 4000 chars
        s3, d3 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": "val-3", "message": "a" * 4001},
        )
        self.assert_check("Message > 4000 characters returns HTTP 422", s3 == 422)

        # Empty session_id
        s4, d4 = make_request(
            f"{self.base_url}/chat",
            method="POST",
            data={"session_id": "", "message": "hello"},
        )
        self.assert_check("Empty session_id returns HTTP 422", s4 == 422)

        # Unknown session 404
        s5, d5 = make_request(f"{self.base_url}/sessions/nonexistent-session-{uuid.uuid4().hex[:8]}/messages")
        self.assert_check("Unknown session returns HTTP 404", s5 == 404)
        self.assert_check(
            "404 returns exact detail: 'session not found'",
            isinstance(d5, dict) and d5.get("detail") == "session not found",
        )

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{BOLD}{CYAN}================================================================={RESET}")
        print(f"{BOLD}CONTRACT VERIFICATION SUMMARY:{RESET}")
        print(f"  Total Checks: {total}")
        print(f"  Passed:       {GREEN}{self.passed}{RESET}")
        print(f"  Failed:       {RED}{self.failed}{RESET}")
        if self.failed == 0:
            print(f"\n  {BOLD}{GREEN}ALL CONTRACT CHECKS PASSED (100% COMPLIANT){RESET}")
        else:
            print(f"\n  {BOLD}{RED}SOME CHECKS FAILED — REVIEW CONTRACT DETAILS ABOVE{RESET}")
        print(f"{BOLD}{CYAN}================================================================={RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Contract Verification Script for Lyftr AI Chatbot")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of backend (default: http://localhost:8000)")
    args = parser.parse_args()

    print_banner(args.base_url)
    verifier = ContractVerifier(args.base_url)
    success = verifier.run_all()
    sys.exit(0 if success else 1)
