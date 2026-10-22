"""Builds src/js/data.js (offline city + country list) from the system tzdata
(zone.tab, iso3166.tab) merged with tools/cities_curated.txt.

Run:  python3 tools/build_data.py [/path/to/zoneinfo]
"""
import json, os, re, sys, unicodedata
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ZI = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/zoneinfo"
OUT = os.path.join(HERE, "..", "src", "js", "data.js")

COUNTRY_OVERRIDES = {
    "GB": "UK", "US": "USA", "AE": "UAE", "KR": "South Korea", "KP": "North Korea",
    "CD": "DR Congo", "CG": "Congo", "CF": "Central African Republic", "CZ": "Czechia",
    "MM": "Myanmar", "SZ": "Eswatini", "AS": "American Samoa", "WS": "Samoa",
    "VG": "British Virgin Islands", "VI": "US Virgin Islands", "TC": "Turks & Caicos",
    "MF": "St Martin", "SX": "Sint Maarten", "CC": "Cocos Islands", "VA": "Vatican City",
}
NAME_FIX = {
    "Ho_Chi_Minh": "Ho Chi Minh City", "St_Johns": "St. John's", "Bahia": "Salvador",
    "Kolkata": "Kolkata", "Port_of_Spain": "Port of Spain", "Vatican": "Vatican City",
    "Isle_of_Man": "Douglas", "Jersey": "St Helier", "Guernsey": "St Peter Port",
    "Kuwait": "Kuwait City", "Mexico_City": "Mexico City", "Macau": "Macau",
    "Panama": "Panama City", "Guatemala": "Guatemala City", "El_Salvador": "San Salvador",
    "Costa_Rica": "San José", "Puerto_Rico": "San Juan", "Luxembourg": "Luxembourg",
    "Monaco": "Monaco", "Singapore": "Singapore", "Hong_Kong": "Hong Kong",
    "Bahrain": "Manama", "Qatar": "Doha", "Belize": "Belize City", "Jamaica": "Kingston",
    "Barbados": "Bridgetown", "Martinique": "Fort-de-France", "Guadeloupe": "Pointe-à-Pitre",
    "Cayman": "George Town", "Anguilla": "The Valley", "Montserrat": "Plymouth",
    "Aruba": "Oranjestad", "Curacao": "Willemstad", "Grenada": "St. George's",
    "Dominica": "Roseau", "Antigua": "St. John's", "Tortola": "Road Town",
    "St_Thomas": "Charlotte Amalie", "St_Lucia": "Castries", "St_Kitts": "Basseterre",
    "St_Vincent": "Kingstown", "Guyana": "Georgetown", "Cayenne": "Cayenne",
    "Reunion": "Saint-Denis", "Mauritius": "Port Louis", "Maldives": "Malé",
    "Mahe": "Victoria", "Comoro": "Moroni", "Mayotte": "Mamoudzou", "Chagos": "Diego Garcia",
    "Christmas": "Flying Fish Cove", "Cocos": "West Island", "Bermuda": "Hamilton",
    "Faroe": "Tórshavn", "Madeira": "Funchal", "Canary": "Las Palmas", "Azores": "Ponta Delgada",
    "South_Georgia": "Grytviken", "Stanley": "Stanley", "St_Helena": "Jamestown",
    "Cape_Verde": "Praia", "Guam": "Hagåtña", "Saipan": "Saipan", "Pago_Pago": "Pago Pago",
    "Tahiti": "Papeete", "Fiji": "Suva", "Efate": "Port Vila", "Guadalcanal": "Honiara",
    "Tongatapu": "Nukuʻalofa", "Palau": "Ngerulmud", "Nauru": "Yaren", "Tarawa": "Tarawa",
    "Majuro": "Majuro", "Kosrae": "Kosrae", "Pohnpei": "Palikir", "Chuuk": "Weno",
    "Norfolk": "Kingston", "Galapagos": "Galápagos", "Easter": "Easter Island",
    "Marquesas": "Marquesas", "Gambier": "Gambier", "Pitcairn": "Adamstown",
    "Wallis": "Mata-Utu", "Funafuti": "Funafuti", "Fakaofo": "Fakaofo", "Niue": "Alofi",
    "Rarotonga": "Avarua", "Kerguelen": "Port-aux-Français", "Chatham": "Chatham Islands",
    "Lord_Howe": "Lord Howe Island", "Macquarie": "Macquarie Island", "Kanton": "Kanton",
    "Kiritimati": "Kiritimati", "Wake": "Wake Island", "Midway": "Midway",
    "Noronha": "Fernando de Noronha", "Thule": "Pituffik", "Danmarkshavn": "Danmarkshavn",
    "Scoresbysund": "Ittoqqortoormiit", "Nuuk": "Nuuk", "Godthab": "Nuuk",
    "Longyearbyen": "Longyearbyen", "Mariehamn": "Mariehamn", "Gibraltar": "Gibraltar",
    "Andorra": "Andorra la Vella", "San_Marino": "San Marino", "Malta": "Valletta",
    "Busingen": "Büsingen", "Vaduz": "Vaduz", "Djibouti": "Djibouti", "Asmara": "Asmara",
    "Bissau": "Bissau", "Sao_Tome": "São Tomé", "El_Aaiun": "Laayoune", "Ceuta": "Ceuta",
}
ADMIN = {
    "America/New_York": "New York", "America/Chicago": "Illinois", "America/Denver": "Colorado",
    "America/Los_Angeles": "California", "America/Phoenix": "Arizona", "America/Anchorage": "Alaska",
    "Pacific/Honolulu": "Hawaii", "America/Detroit": "Michigan", "America/Boise": "Idaho",
    "America/Juneau": "Alaska", "America/Sitka": "Alaska", "America/Nome": "Alaska",
    "America/Adak": "Alaska", "America/Yakutat": "Alaska", "America/Metlakatla": "Alaska",
    "America/Toronto": "Ontario", "America/Vancouver": "British Columbia",
    "America/Edmonton": "Alberta", "America/Winnipeg": "Manitoba", "America/Halifax": "Nova Scotia",
    "America/Regina": "Saskatchewan", "America/St_Johns": "Newfoundland",
    "Australia/Sydney": "New South Wales", "Australia/Melbourne": "Victoria",
    "Australia/Brisbane": "Queensland", "Australia/Perth": "Western Australia",
    "Australia/Adelaide": "South Australia", "Australia/Hobart": "Tasmania",
    "Australia/Darwin": "Northern Territory",
}

def norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)).lower())

def coord(s, deg_len):
    sign = -1 if s[0] == "-" else 1
    d = s[1:]
    deg = int(d[:deg_len]); mins = int(d[deg_len:deg_len + 2])
    secs = int(d[deg_len + 2:deg_len + 4]) if len(d) > deg_len + 2 else 0
    return round(sign * (deg + mins / 60 + secs / 3600), 2)

def parse_coords(c):
    m = re.match(r"([+-]\d+)([+-]\d+)", c)
    lat, lng = m.group(1), m.group(2)
    return coord(lat, 2), coord(lng, 3)

def rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                yield line.rstrip("\n").split("\t")

version = open(os.path.join(ZI, "tzdata.zi"), encoding="utf-8").readline().split()[-1] \
    if os.path.exists(os.path.join(ZI, "tzdata.zi")) else "unknown"
countries = {r[0]: r[1] for r in rows(os.path.join(ZI, "iso3166.tab"))}
countries.update(COUNTRY_OVERRIDES)

zone_cc = {}
cities, seen = [], set()
problems = []

# 1. curated list wins
for line in open(os.path.join(HERE, "cities_curated.txt"), encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    names, admin, cc, lat, lng, tz, rank = [p.strip() for p in line.split("|")]
    names = names.split("/")
    try:
        ZoneInfo(tz)
    except Exception:
        problems.append(f"unknown zone {tz} for {names[0]}")
    if cc not in countries:
        problems.append(f"unknown country {cc} for {names[0]}")
    key = norm(names[0]) + cc
    if key in seen:
        problems.append(f"duplicate {names[0]} {cc}")
    seen.add(key)
    for n in names:
        seen.add(norm(n) + cc)
    cities.append([names[0], admin, cc, float(lat), float(lng), tz, int(rank), "|".join(names[1:])])

# 2. one entry per tzdata zone (covers every country)
for r in rows(os.path.join(ZI, "zone.tab")):
    cc, coords, tz = r[0], r[1], r[2]
    zone_cc[tz] = cc
    area = tz.split("/")[0]
    if area in ("Antarctica", "Etc"):
        continue
    last = tz.split("/")[-1]
    name = NAME_FIX.get(last, last.replace("_", " "))
    key = norm(name) + cc
    if key in seen:
        continue
    seen.add(key)
    lat, lng = parse_coords(coords)
    rank = 3 if tz.count("/") >= 2 else 2
    cities.append([name, ADMIN.get(tz, ""), cc, lat, lng, tz, rank, ""])

# sanity: curated zone should belong to the same country in zone.tab (links excepted)
for c in cities:
    zcc = zone_cc.get(c[5])
    if zcc and zcc != c[2]:
        problems.append(f"zone/country mismatch: {c[0]} {c[2]} -> {c[5]} ({zcc})")

cities.append(["UTC", "", "", 51.48, 0.0, "UTC", 2, "GMT|Coordinated Universal Time|Zulu"])

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"// Generated by tools/build_data.py from tzdata {version} + tools/cities_curated.txt. Do not edit by hand.\n")
    f.write("window.WT = window.WT || {};\n")
    f.write(f"WT.TZDATA_VERSION = {json.dumps(version)};\n")
    f.write("WT.COUNTRIES = " + json.dumps(countries, ensure_ascii=False, separators=(",", ":")) + ";\n")
    f.write("// [name, admin, country, lat, lng, zone, rank, aliases]\n")
    f.write("WT.CITIES = [\n")
    f.write(",\n".join(json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in cities))
    f.write("\n];\n")

print(f"tzdata {version}: {len(cities)} cities, {len(countries)} countries -> {os.path.relpath(OUT)}")
for p in problems:
    print("WARN", p)
