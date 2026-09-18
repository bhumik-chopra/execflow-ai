"""Single Groq boundary. One request per operation; no automatic retries."""
import json
from typing import Any
from groq import AsyncGroq, APIError, AuthenticationError, RateLimitError
from pydantic import BaseModel
from config import Settings

class LLMError(RuntimeError):
    status_code = 503
class LLMUnavailable(LLMError):
    def __init__(self): super().__init__('AI processing is temporarily unavailable.')
class LLMRateLimitError(LLMError):
    status_code = 429
    def __init__(self): super().__init__('AI rate limit reached. Please try again later.')
class LLMResponseError(LLMError):
    status_code = 502
    def __init__(self): super().__init__('AI returned an invalid response. Please try again later.')
class LLMAuthenticationError(LLMError):
    def __init__(self): super().__init__('AI credentials need attention on the backend.')
LLMConfigurationError = LLMUnavailable
LLMRequestError = LLMUnavailable

def parse_json(raw):
    data = json.loads(raw)
    if not isinstance(data, dict): raise ValueError('Expected JSON object')
    return data

class LLMService:
    def __init__(self, settings: Settings):
        self.model = settings.groq_model
        key = settings.groq_api_key.get_secret_value().strip()
        self._client = AsyncGroq(api_key=key, max_retries=0, timeout=45) if key else None
    async def ping(self):
        return self._client is not None
    async def _generate(self, prompt, *, json_mode=False, system_prompt=None):
        if self._client is None: raise LLMUnavailable()
        kwargs = {'response_format': {'type': 'json_object'}} if json_mode else {}
        try:
            response = await self._client.chat.completions.create(model=self.model,
                messages=[{'role':'system','content':system_prompt or 'Answer using only supplied evidence.'}, {'role':'user','content':prompt}],
                temperature=0, max_tokens=3500, **kwargs)
            if response.choices[0].finish_reason == 'length': raise LLMResponseError()
            content = response.choices[0].message.content
            if not content: raise LLMResponseError()
            return content
        except RateLimitError: raise LLMRateLimitError() from None
        except AuthenticationError: raise LLMAuthenticationError() from None
        except APIError: raise LLMUnavailable() from None
    async def generate(self, prompt, *, system_prompt=None):
        return await self._generate(prompt, system_prompt=system_prompt)
    async def generate_json(self, prompt, response_model: type[BaseModel] | None=None, *, use_json_schema=True, system_prompt=None) -> dict[str, Any]:
        instructions = (system_prompt or '') + '\nReturn one JSON object.'
        if response_model:
            instructions += '\nSchema: ' + json.dumps(response_model.model_json_schema(), separators=(',', ':'))
        raw = await self._generate(prompt, json_mode=True, system_prompt=instructions)
        try:
            data = parse_json(raw)
            return response_model.model_validate(data).model_dump(mode='json') if response_model else data
        except ValueError: raise LLMResponseError() from None
    async def close(self):
        if self._client: await self._client.close()
