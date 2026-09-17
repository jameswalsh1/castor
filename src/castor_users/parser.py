import pandas as pd
from bs4 import BeautifulSoup

from castor_users.models import CastorUser, RoleAssignment, Site, Study, StudyUser

USER_COLUMNS = [
    "Study ID", "Site", "Code", "Abbreviation", "Country", "Main Site",
    "User", "Email", "Role", "Two Factor Authentication", "Last login",
]


def _text(element) -> str:
    return element.get_text(" ", strip=True)


def extract_users(html: str, study_id: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    outer_table = None
    for table in soup.find_all("table"):
        thead = table.find("thead")
        row = thead.find("tr") if thead else None
        headers = [_text(cell) for cell in row.find_all("th", recursive=False)] if row else []
        if headers == ["Site", "Users"]:
            outer_table = table
            break
    if outer_table is None:
        raise RuntimeError("Could not find Site / Users table.")

    tbody = outer_table.find("tbody")
    if tbody is None:
        raise RuntimeError("Site / Users table has no tbody.")

    records: list[dict[str, str]] = []
    for row in tbody.find_all("tr", recursive=False):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 2:
            continue
        site_cell, users_cell = cells
        metadata = {key: "" for key in ("Code", "Abbreviation", "Country", "Main Site")}
        metadata_table = site_cell.find("table")
        if metadata_table:
            for metadata_row in metadata_table.find_all("tr"):
                metadata_cells = metadata_row.find_all("td")
                if len(metadata_cells) == 2:
                    key = _text(metadata_cells[0]).rstrip(":")
                    if key in metadata:
                        metadata[key] = _text(metadata_cells[1])

        users_table = users_cell.find("table")
        users_thead = users_table.find("thead") if users_table else None
        users_tbody = users_table.find("tbody") if users_table else None
        if users_thead is None or users_tbody is None:
            continue
        header_row = users_thead.find("tr")
        if header_row is None:
            continue
        headers = [_text(cell) for cell in header_row.find_all("th", recursive=False)]
        for user_row in users_tbody.find_all("tr", recursive=False):
            user_cells = user_row.find_all("td", recursive=False)
            if len(user_cells) != len(headers):
                continue
            user = dict(zip(headers, (_text(cell) for cell in user_cells)))
            raw_row = {
                "Study ID": study_id,
                "Site": _text(site_cell.find("strong")) if site_cell.find("strong") else "",
                **metadata,
                "User": user.get("User", ""),
                "Email": user.get("Email", ""),
                "Role": user.get("Role", ""),
                "Two Factor Authentication": user.get("Two Factor Authentication", ""),
                "Last login": user.get("Last login", ""),
            }
            records.append(CastorUser.model_validate(raw_row).model_dump(by_alias=True))
    return pd.DataFrame.from_records(records, columns=USER_COLUMNS)


def users_to_dataframe(
    study: Study,
    users: list[StudyUser],
    sites: list[Site],
) -> pd.DataFrame:
    sites_by_id = {site.site_id or site.id: site for site in sites}
    records: list[dict[str, str]] = []

    for user in users:
        assignments: list[RoleAssignment | None] = [*user.role_assignments]
        if not assignments:
            assignments.append(user.default_role_assignment)
        assignments = [assignment for assignment in assignments if assignment is not None]
        if not assignments:
            assignments = [None]

        for assignment in assignments:
            site = sites_by_id.get(assignment.site_id, Site()) if assignment else Site()
            raw_last_login = user.last_login
            last_login = (
                raw_last_login.get("date", "")
                if isinstance(raw_last_login, dict)
                else raw_last_login
            )
            row = {
                "Study ID": study.study_id,
                "Site": site.name or "Study-wide",
                "Code": site.code,
                "Abbreviation": site.abbreviation,
                "Country": site.country,
                "Main Site": "",
                "User": user.full_name,
                "Email": user.email_address,
                "Role": assignment.role_name if assignment else "",
                "Two Factor Authentication": "",
                "Last login": last_login,
            }
            records.append(CastorUser.model_validate(row).model_dump(by_alias=True))

    return pd.DataFrame.from_records(records, columns=USER_COLUMNS)