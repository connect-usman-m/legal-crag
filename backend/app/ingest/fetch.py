import hashlib
import urllib.request
from pathlib import Path

from app.core.config import Settings

SOURCES = {
    "gdpr.pdf": "https://op.europa.eu/o/opportal-service/download-handler?identifier=3e485e15-11bd-11e6-ba9a-01aa75ed71a1&format=pdfa1a&language=en&productionSystem=cellar",
    "edpb_consent_05_2020.pdf": "https://www.edpb.europa.eu/system/files/documents/files/file1/edpb_guidelines_202005_consent_en.pdf",
    "edpb_breach_09_2022.pdf": "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_202209_personal_data_breach_notification_v2.0_en.pdf",
    "edpb_access_01_2022.pdf": "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_202201_data_subject_rights_access_v2_en.pdf",
}


def download(url: str, destination: Path) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "LexGate/0.1 ingestion"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    if len(payload) < 1000:
        raise ValueError(f"Downloaded too few bytes from {url}")
    destination.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    settings = Settings()
    raw_dir = Path(settings.chroma_dir).parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in SOURCES.items():
        destination = raw_dir / filename
        if destination.exists() and destination.stat().st_size > 1000:
            print(f"Using cached {filename}")
            continue
        checksum = download(url, destination)
        print(f"Saved {filename} sha256={checksum[:12]}")


if __name__ == "__main__":
    main()
