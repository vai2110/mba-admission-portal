from pathlib import Path

from bs4 import BeautifulSoup


def main() -> None:
    target_file = Path("changed-html.txt")
    if not target_file.exists():
        print("No audit target file found; nothing to verify.")
        return

    pages = [p.strip() for p in target_file.read_text(encoding="utf-8").splitlines() if p.strip()]
    if not pages:
        print("No newly created pages awaiting verification.")
        return

    for name in pages:
        path = Path(name)
        if not path.exists():
            raise SystemExit(f"Missing generated page: {name}")

        raw = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "html.parser")

        if raw.lower().count("<html") != 1:
            raise SystemExit(f"HTML integrity failed: {name} — expected exactly one <html> element")
        if not soup.find("title"):
            raise SystemExit(f"HTML integrity failed: {name} — title missing")
        if not soup.find("h1"):
            raise SystemExit(f"HTML integrity failed: {name} — H1 missing")
        if not soup.find("meta", attrs={"name": "description"}):
            raise SystemExit(f"HTML integrity failed: {name} — meta description missing")
        if not soup.find("link", attrs={"rel": "canonical"}):
            raise SystemExit(f"HTML integrity failed: {name} — canonical missing")

        print(f"Integrity PASS: {name}")


if __name__ == "__main__":
    main()
