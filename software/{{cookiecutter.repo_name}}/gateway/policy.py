"""Where a request may go, decided before it leaves the gateway.

The caller states what the content is in the request's metadata:
``{"metadata": {"visibility": "public" | "private" | "unknown"}}``.
Public content may go to any model. Anything else, including a request
that says nothing, may go only to a model whose name starts with
``local/``. A refusal is an HTTP 403 naming the rule; nothing is rerouted.

The caller states the visibility, so this guards against mistakes, not
against a caller who lies. Who may call at all is the master key's job.
"""

from typing import Any

# FastAPI and LiteLLM are installed in the gateway's image, not in this
# project's environment, so the linters cannot import them.
# pylint: disable=import-error
from fastapi import HTTPException
from litellm.integrations.custom_logger import CustomLogger

# pylint: enable=import-error

LOCAL_PREFIX = "local/"
VISIBILITIES = ("public", "private", "unknown")


def refusal(model: str, visibility: object) -> str | None:
    """Return why content may not go to a model, or None if it may.

    Args:
        model: The model name the request asks for.
        visibility: The caller's stated visibility; None counts as unknown.

    Returns:
        A sentence naming the rule broken, or None.
    """
    stated = "unknown" if visibility is None else visibility
    if stated not in VISIBILITIES:
        return f"visibility must be one of {', '.join(VISIBILITIES)}"
    if stated == "public" or model.startswith(LOCAL_PREFIX):
        return None
    return (
        f"{stated} content may go only to a {LOCAL_PREFIX} model, "
        f"not to {model}"
    )


# LiteLLM calls the one hook below; the class needs no other method.
# pylint: disable-next=too-few-public-methods
class VisibilityPolicy(CustomLogger):  # type: ignore[misc]
    """Refuse a request whose content may not reach the model it names."""

    async def async_pre_call_hook(
        self,
        user_api_key_dict: Any,
        cache: Any,
        data: dict[str, Any],
        call_type: str,
    ) -> dict[str, Any]:
        """Pass the request on, or raise a 403 with the rule it broke."""
        # LiteLLM fixes this signature; only `data` is needed here.
        del user_api_key_dict, cache, call_type
        metadata = data.get("metadata") or {}
        reason = refusal(
            str(data.get("model", "")), metadata.get("visibility")
        )
        if reason is not None:
            raise HTTPException(status_code=403, detail=reason)
        return data


# LiteLLM loads callbacks by name from the config's folder: an instance.
visibility_policy = VisibilityPolicy()
