from pathlib import Path

from ted.crypto import decrypt_ted
from ted.reader import get_team_summary

ted_path = Path("chelsea.ted")

raw = ted_path.read_bytes()
data = decrypt_ted(raw)

summary = get_team_summary(data)

print(summary["teamName"])
print(summary["countryId"])
