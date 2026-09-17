from pydantic import BaseModel, ConfigDict, Field, field_validator


class CastorUser(BaseModel):
    """A user row extracted from the Castor permissions page."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    study_id: str = Field(alias="Study ID", min_length=1)
    site: str = Field(alias="Site", min_length=1)
    code: str = Field(default="", alias="Code")
    abbreviation: str = Field(default="", alias="Abbreviation")
    country: str = Field(default="", alias="Country")
    main_site: str = Field(default="", alias="Main Site")
    user: str = Field(alias="User", min_length=1)
    email: str = Field(default="", alias="Email")
    role: str = Field(default="", alias="Role")
    two_factor_authentication: str = Field(
        default="",
        alias="Two Factor Authentication",
    )
    last_login: str = Field(default="", alias="Last login")

    @field_validator(
        "code",
        "abbreviation",
        "country",
        "main_site",
        "email",
        "role",
        "two_factor_authentication",
        "last_login",
        mode="before",
    )
    @classmethod
    def empty_missing_values(cls, value: object) -> str:
        return "" if value is None else str(value)


class Study(BaseModel):
    model_config = ConfigDict(extra="ignore")

    study_id: str
    name: str = ""


class Site(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    site_id: str = ""
    name: str = ""
    abbreviation: str = ""
    code: str = ""
    country: str = ""

    @field_validator("id", "site_id", "name", "abbreviation", "code", "country", mode="before")
    @classmethod
    def empty_null_values(cls, value: object) -> str:
        return "" if value is None else str(value)


class RoleAssignment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    site_id: str = ""
    role_name: str = ""


class StudyUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str = ""
    email_address: str = ""
    last_login: object = ""
    default_role_assignment: RoleAssignment | None = None
    role_assignments: list[RoleAssignment] = []