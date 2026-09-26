from typing import AsyncGenerator

from pydantic import PrivateAttr
from google.adk.models.base_llm import BaseLlm
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse


class FallbackLlm(BaseLlm):
    """Model router: tries each model in order; on rate-limit or any error,
    silently falls back to the next. List them best-quality first."""

    _sub_models: list = PrivateAttr(default_factory=list)

    def __init__(self, model_names: list[str], **kwargs):
        super().__init__(model=model_names[0], **kwargs)  # BaseLlm needs a label
        self._sub_models = [LiteLlm(model=name) for name in model_names]

    @classmethod
    def supported_models(cls) -> list[str]:
        return []

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        last_error = None
        for sub in self._sub_models:
            try:
                # Buffer the whole answer so a mid-way failure never leaks half
                # a response before we fall back to the next model.
                responses = []
                async for resp in sub.generate_content_async(llm_request, stream=False):
                    responses.append(resp)
                for resp in responses:
                    yield resp
                return  # this model succeeded — stop here
            except Exception as e:
                last_error = e
                print(f"[FallbackLlm] {sub.model} failed "
                      f"({type(e).__name__}); trying next model.")
                continue
        if last_error:
            raise last_error