from collections.abc import Iterator
from urllib.parse import urljoin

import requests

from castor_users.config import Settings
from castor_users.models import Study


class CastorApiClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def authenticate(self) -> None:
        response = self.session.post(
            f"{self.settings.api_base_url}/oauth/token",
            data={
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Castor OAuth response did not contain an access token.")
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.settings.timeout_seconds)
        if response.ok:
            return response
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None
        if detail:
            raise RuntimeError(
                f"Castor API request failed ({response.status_code}): {detail}"
            ) from None
        response.raise_for_status()
        return response

    def _hal_items(self, path: str, key: str) -> Iterator[dict]:
        url = f"{self.settings.api_base_url}/api/{path.lstrip('/')}"
        while url:
            payload = self._get(url).json()
            yield from payload.get("_embedded", {}).get(key, [])
            url = payload.get("_links", {}).get("next", {}).get("href")
            if url:
                url = urljoin(self.settings.api_base_url, url)

    def list_studies(self) -> list[Study]:
        return [Study.model_validate(item) for item in self._hal_items("study", "study")]
