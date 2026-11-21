
"""Privacy-first Langfuse tracing. No telemetry is sent without credentials."""

import os
import logging

log = logging.getLogger(__name__)


def initialize():
    """Call once, before instrumented app modules are loaded."""
    from dotenv import load_dotenv
    load_dotenv()

    if (
        not os.getenv("LANGFUSE_PUBLIC_KEY")
        or not os.getenv("LANGFUSE_SECRET_KEY")
        or os.getenv("LANGFUSE_DISABLED", "false").lower() in ("1", "true", "yes")
    ):
        log.info("Langfuse observability disabled (no keys or kill switch)")
        return

    try:
        from langfuse import get_client

        get_client()
        log.info("Langfuse observability enabled")

    except Exception:
        log.exception(
            "Langfuse initialization failed; application will continue without telemetry"
        )


def trace(name):
    """Trace sync/async functions without capturing inputs or outputs."""

    def decorate(fn):
        try:
            from langfuse import observe

            return observe(
                name=name,
                capture_input=False,
                capture_output=False,
            )(fn)

        except ImportError:
            return fn

    return decorate
