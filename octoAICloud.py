from typing import Any, Dict, List, Mapping, Optional
import requests
from pydantic import Extra, root_validator

from langchain.llms.base import LLM
from langchain.utils import get_from_dict_or_env
from langchain.llms.utils import enforce_stop_tokens
from langchain.callbacks.manager import CallbackManagerForLLMRun


class OctoAiCloudLLM(LLM):
    """
    OctoAiCloudLLM is a class to interact with OctoAI Cloud's language models.
    It extends the base LLM class from langchain.
    """
    endpoint_url: str = ""
    """Endpoint URL to use."""
    task: Optional[str] = None
    """Task to call the model with. Should be a task that returns `generated_text`."""
    model_kwargs: Optional[dict] = None
    """Key word arguments to pass to the model."""
    octoai_api_token: Optional[str] = None

    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        values["octoai_api_token"] = get_from_dict_or_env(
            values, "octoai_api_token", "OCTOAI_API_TOKEN")
        values["endpoint_url"] = get_from_dict_or_env(
            values, "endpoint_url", "ENDPOINT_URL")
        return values

    @property
    def _llm_type(self) -> str:
        """Return the type of the language model."""
        return "octoai_cloud_llm"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "endpoint_url": self.endpoint_url,
            "task": self.task,
            "model_kwargs": self.model_kwargs or {},
        }

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """
        Call out to inference endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.
        """
        # Prepare the payload
        parameter_payload = {"prompt": prompt,
                             "parameters": self.model_kwargs or {}}

        # Prepare the headers
        headers = {
            "Authorization": f"Bearer {self.octoai_api_token}",
            "Content-Type": "application/json",
        }

        # Send the request
        try:
            response = requests.post(
                self.endpoint_url, headers=headers, json=parameter_payload
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error raised by inference endpoint: {e}") from e

        # Extract the generated text
        generated_text = response.json()
        if "error" in generated_text:
            raise ValueError(
                f"Error raised by inference API: {generated_text['error']}"
            )

        # Enforce stop tokens if provided
        text = generated_text["generated_text"]
        if stop is not None:
            text = enforce_stop_tokens(text, stop)

        return text