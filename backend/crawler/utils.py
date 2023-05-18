

def normalize_url(url: str) -> str:
    return url.replace("https://voz.vn/", "").strip("/")