from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    web_base_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    output_path: str = "castor_users.csv"
    timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "Settings":
        required = {
            "client_id": "CASTOR_CLIENT_ID",
            "client_secret": "CASTOR_CLIENT_SECRET",
            "username": "CASTOR_USERNAME",
            "password": "CASTOR_PASSWORD",
        }
        values: dict[str, str] = {}
        missing: list[str] = []
        for field, variable in required.items():
            value = os.getenv(variable, "").strip()
            if not value:
                missing.append(variable)
            values[field] = value
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(
            api_base_url=os.getenv("CASTOR_API_BASE_URL", "https://uk.castoredc.com").rstrip("/"),
            web_base_url=os.getenv("CASTOR_WEB_BASE_URL", "https://uk.castoredc.com").rstrip("/"),
            output_path=os.getenv("CASTOR_OUTPUT", "castor_users.csv"),
            client_id=values["client_id"],
            client_secret=values["client_secret"],
            username=values["username"],
            password=values["password"],
        )