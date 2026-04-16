from urllib.parse import urlparse
from backend.db.postgres import get_conn


def normalize_domain_from_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    raw_url = raw_url.strip()

    if not raw_url.startswith(("http://", "https://")):
        raw_url = "http://" + raw_url

    parsed = urlparse(raw_url)
    domain = parsed.netloc.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def lookup_domain(domain: str) -> dict:
    if not domain:
        return {
            "domain": "",
            "found": False,
            "is_known_safe": False,
            "is_known_suspicious": False,
            "source_name": None,
            "category": None,
            "risk_note": None,
        }

    conn = get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT domain, source_name, category, is_known_safe,
                       is_known_suspicious, risk_note
                FROM domain_intelligence
                WHERE domain = %s
                """,
                (domain,)
            )
            row = cur.fetchone()

            if not row:
                return {
                    "domain": domain,
                    "found": False,
                    "is_known_safe": False,
                    "is_known_suspicious": False,
                    "source_name": None,
                    "category": None,
                    "risk_note": None,
                }

            return {
                "domain": row[0],
                "found": True,
                "is_known_safe": bool(row[3]),
                "is_known_suspicious": bool(row[4]),
                "source_name": row[1],
                "category": row[2],
                "risk_note": row[5],
            }

    finally:
        conn.close()