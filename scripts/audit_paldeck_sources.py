import re
import urllib.request
from html import unescape


USER_AGENT = "pal-database-audit/1.0 (+https://pal-database.pages.dev/)"
THGL_EN_URL = "https://palworld.th.gl/db/paldeck"
PALDB_URL = "https://paldb.cc/en/Pals"
PALWORLD_GG_URL = "https://palworld.gg/pals"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def text(value):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<.*?>", " ", value))).strip()


def normalize_name(value):
    return re.sub(r"^NEW\s+", "", value).strip()


def parse_thgl_en(html):
    rows = []
    seen = set()
    pattern = re.compile(
        r'<a class="flex items-center gap-2 [^"]*" href="/db/paldeck/([^"]+)".*?'
        r'<span class="truncate text-sm">([^<]+)</span>',
        re.S,
    )
    for pal_id, name in pattern.findall(html):
        pal_id = unescape(pal_id).strip()
        name = unescape(name).strip()
        if pal_id and name and pal_id not in seen:
            seen.add(pal_id)
            rows.append({"id": pal_id, "name": name})
    return rows


def parse_paldb(html):
    rows = []
    seen = set()
    pattern = re.compile(
        r'<span class="text-white-50 small">#([^<]+)</span>\s*'
        r'<a class="itemname"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        re.S,
    )
    for number, slug, name in pattern.findall(html):
        row = {
            "number": unescape(number).strip(),
            "slug": unescape(slug).strip(),
            "name": unescape(name).strip(),
        }
        key = (row["number"], row["name"])
        if key not in seen:
            seen.add(key)
            rows.append(row)
    return rows


def parse_palworld_gg(html):
    rows = []
    seen = set()
    pattern = re.compile(r'<a[^>]+href="/pal/([^"]+)"[^>]*>(.*?)</a>', re.S)
    for slug, body in pattern.findall(html):
        label = text(body)
        match = re.match(r"(.+?)\s+#([0-9]+[A-Z]?)\b", label)
        if not match:
            continue
        row = {
            "number": match.group(2),
            "slug": unescape(slug).strip(),
            "name": normalize_name(match.group(1)),
        }
        key = (row["number"], row["name"])
        if key not in seen:
            seen.add(key)
            rows.append(row)
    return rows


def print_diff(label, reference_rows, candidate_rows):
    reference_names = {row["name"] for row in reference_rows}
    candidate_names = {row["name"] for row in candidate_rows}
    missing = sorted(reference_names - candidate_names)
    extra = sorted(candidate_names - reference_names)
    print(f"{label} missing_from_candidate={len(missing)} extra_in_candidate={len(extra)}")
    if missing:
        print("  missing:", ", ".join(missing))
    if extra:
        print("  extra:", ", ".join(extra))


def main():
    thgl = parse_thgl_en(fetch(THGL_EN_URL))
    paldb = parse_paldb(fetch(PALDB_URL))
    palworld_gg = parse_palworld_gg(fetch(PALWORLD_GG_URL))

    print(f"TH.GL EN: {len(thgl)}")
    print(f"PalDB: {len(paldb)}")
    print(f"Palworld.gg: {len(palworld_gg)}")
    print_diff("PalDB vs TH.GL", paldb, thgl)
    print_diff("Palworld.gg vs TH.GL", palworld_gg, thgl)
    print_diff("PalDB vs Palworld.gg", paldb, palworld_gg)


if __name__ == "__main__":
    main()
