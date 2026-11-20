import json
import logging
import os
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.environ["XKCD_BASE_URL"].rstrip("/")
REQUEST_TIMEOUT = float(os.environ["XKCD_REQUEST_TIMEOUT"])
REQUEST_DELAY = float(os.environ["XKCD_REQUEST_DELAY"])
MAX_RETRIES = int(os.environ["XKCD_MAX_RETRIES"])
START_ID = int(os.environ["XKCD_START_ID"])
END_ID = int(os.environ["XKCD_END_ID"])
RAW_DIR = Path(os.environ["XKCD_RAW_DIR"])

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)
log = logging.getLogger("xkcd-downloader")

def get_session() -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total = MAX_RETRIES,
        backoff_factor = 1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))

    session.headers.update({
        "User-Agent": "xkcd-bigdata-course-downloader/1.0"
    })

    return session


def get_comic(
        session: requests.Session,
        comic_id: int
) -> dict | None:

    response = session.get(
        f"{BASE_URL}/{comic_id}/info.0.json",
        timeout=REQUEST_TIMEOUT
    )

    if response.status_code == 404:
        log.info("Comic %d nicht vorhanden (404)", comic_id)
        return None

    response.raise_for_status()
    return response.json()

def main() -> None:
    if START_ID < 1 or END_ID < 0 or REQUEST_DELAY < 0:
        raise ValueError("Ungültige Download-Einstellungen")

    with get_session() as session:
        # Ermittle aktuellste Comic-ID
        if END_ID == 0:
            response = session.get(
                f"{BASE_URL}/info.0.json",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            end_id = int(response.json()["num"])
        else:
            end_id = END_ID

        downloaded = skipped = failed = 0

        for comic_id in range(START_ID, end_id + 1):
            # heruntergleadene dateien überspringen
            if list(RAW_DIR.glob(f"*/{comic_id}.json")):
                skipped += 1
                continue

            try:
                comic = get_comic(session, comic_id)

                if comic is None:
                    skipped += 1
                    continue

                year = str(int(comic["year"]))
                folder = RAW_DIR / year
                folder.mkdir(parents=True, exist_ok=True)

                file_path = folder / f"{comic_id}.json"
                temp_path = folder / f"{comic_id}.json.tmp"

                # temp speichern
                with temp_path.open("w", encoding="utf-8") as file:
                    json.dump(
                        comic,
                        file,
                        ensure_ascii=False,
                        indent=2
                    )

                # persistent speichern
                temp_path.replace(file_path)

                downloaded +=1
                log.info(
                    "Comic %d gespeichert: %s",
                    comic_id,
                    file_path
                )

            except(
                requests.RequestException,
                ValueError,
                KeyError,
                OSError
            ) as error:
                failed += 1
                log.error(
                    "Comic %d fehlgeschlagen %s",
                    comic_id,
                    error
                )

            finally:
                time.sleep(REQUEST_DELAY)

        log.info("Fertig: %d heruntergeladen, "
                 "%d überspringen, %d Fehler",
                 downloaded,
                 skipped,
                 failed)
        if failed:
            raise SystemExit(1)

if __name__ == "__main__":
    main()
