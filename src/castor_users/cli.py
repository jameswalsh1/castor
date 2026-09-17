import argparse
import logging

import pandas as pd
import requests

from castor_users.client import CastorApiClient
from castor_users.config import Settings
from castor_users.parser import USER_COLUMNS, extract_users
from castor_users.web_client import CastorWebClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="CSV output path (defaults to CASTOR_OUTPUT).")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        args = build_parser().parse_args()
        settings = Settings.from_environment()
        output_path = args.output or settings.output_path
        client = CastorApiClient(settings)
        client.authenticate()
        studies = client.list_studies()
        web_client = CastorWebClient(settings)
        web_client.authenticate()
        frames = [
            extract_users(web_client.get_permissions_page(study.study_id), study.study_id)
            for study in studies
        ]
        users = (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame(columns=USER_COLUMNS)
        )
        users.to_csv(output_path, index=False)
        logging.info(
            "Exported %d users across %d studies to %s",
            len(users),
            len(studies),
            output_path,
        )
    except (ValueError, RuntimeError, requests.RequestException) as error:
        logging.error("Export failed: %s", error)
        raise SystemExit(1) from None