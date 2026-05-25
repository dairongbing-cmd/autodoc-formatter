import chardet


def detect_and_read(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read()

    if not raw:
        return ""

    result = chardet.detect(raw)
    encoding = result.get("encoding") or "utf-8"
    confidence = result.get("confidence", 0)

    fallback_encodings = ["utf-8", "utf-16", "latin-1", "windows-1252", "gbk"]
    if encoding.lower() not in fallback_encodings:
        fallback_encodings.insert(0, encoding.lower())

    for enc in fallback_encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw.decode("utf-8", errors="replace")
