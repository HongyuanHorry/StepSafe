import pandas as pd
from urllib.parse import urlparse

INPUT_CSV = "verified_online.csv"
OUTPUT_CSV = "domain_intelligence_ready.csv"


def extract_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1"}


def main():
    df = pd.read_csv(INPUT_CSV)

    # Create target columns
    df["domain"] = df["url"].apply(extract_domain)
    df["source_url"] = df["url"].astype(str)
    df["source_name"] = "verified_online"
    df["category"] = df["target"].fillna("phishing").astype(str)

    # Treat verified phishing records as suspicious
    df["is_known_safe"] = False
    df["is_known_suspicious"] = df["verified"].apply(to_bool)

    df["risk_note"] = df.apply(
        lambda row: f"Verified phishing record. Target: {row['target']}. Online: {row['online']}",
        axis=1
    )

    # Keep only verified suspicious rows with valid domains
    df = df[(df["domain"] != "") & (df["is_known_suspicious"] == True)].copy()

    # Remove duplicates by domain
    df = df.drop_duplicates(subset=["domain"], keep="first")

    final_df = df[
        [
            "domain",
            "source_url",
            "source_name",
            "category",
            "is_known_safe",
            "is_known_suspicious",
            "risk_note",
        ]
    ].copy()

    print("Rows ready for import:", len(final_df))
    print(final_df.head())

    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved cleaned CSV to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()