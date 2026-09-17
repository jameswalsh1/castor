"""Requests-based Castor web client for permissions pages."""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from castor_users.config import Settings


class CastorWebClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                )
            }
        )

    def authenticate(self) -> None:
        response = self.session.get(
            f"{self.settings.web_base_url}/castor-identity/authenticate",
            params={"login_hint": self.settings.username, "deeplink": ""},
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        form = BeautifulSoup(response.text, "html.parser").find("form")
        if not isinstance(form, Tag):
            raise RuntimeError("Could not find Castor Identity login form.")

        action = form.get("action")
        if not isinstance(action, str) or not action:
            raise RuntimeError("Login form does not contain an action.")

        data: dict[str, str] = {}
        for field in form.find_all("input"):
            name = field.get("name")
            if not isinstance(name, str) or field.has_attr("disabled"):
                continue
            field_type = field.get("type", "text")
            field_type = field_type if isinstance(field_type, str) else "text"
            if field_type.lower() == "password":
                data[name] = self.settings.password
            elif "username" in name.lower() or "email" in name.lower():
                data[name] = self.settings.username
            elif field_type.lower() not in {"submit", "button"}:
                value = field.get("value", "")
                data[name] = value if isinstance(value, str) else ""

        login_response = self.session.post(
            urljoin(response.url, action),
            data=data,
            timeout=self.settings.timeout_seconds,
        )
        login_response.raise_for_status()

        verification = self.session.get(
            f"{self.settings.web_base_url}/user/user",
            timeout=self.settings.timeout_seconds,
        )
        verification.raise_for_status()
        if "Castor Log In" in verification.text or not self.session.cookies.get("PHPSESSID"):
            raise RuntimeError("Web authentication failed: no authenticated Castor session was created.")

    def get_permissions_page(self, study_id: str) -> str:
        response = self.session.get(
            f"{self.settings.web_base_url}/list-crf-rights/{study_id}",
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        if "Castor Log In" in response.text:
            raise RuntimeError("Web session is not authenticated.")
        if "Permissions overview" not in response.text:
            raise RuntimeError(f"Permissions page was not returned for study {study_id}.")
        return response.text