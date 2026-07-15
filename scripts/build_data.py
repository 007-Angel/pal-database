import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TECH_URL = "https://docs.palworldgame.com/settings-and-operation/technologyids/"
RECIPES_URL = "https://palworld.th.gl/zh-CN/db/recipes"
PALDECK_10_URL = "https://palworld.th.gl/zh-CN/db/paldeck"
PALDECK_10_EN_URL = "https://palworld.th.gl/db/paldeck"
PALDB_PALS_URL = "https://paldb.cc/en/Pals"
PALDB_EN_BASE_URL = "https://paldb.cc/en/"
PALDB_CN_BASE_URL = "https://paldb.cc/cn/"
PALDECK_10_SUPPLEMENTS = RAW_DIR / "paldeck-1.0-supplements.zh-CN.json"


TYPE_NAMES = {
    "neutral": "无属性",
    "fire": "火",
    "water": "水",
    "grass": "草",
    "electric": "雷",
    "ice": "冰",
    "ground": "地",
    "dark": "暗",
    "dragon": "龙",
}

THGL_ELEMENT_NAMES = {
    "Dark": "暗",
    "Dragon": "龙",
    "Earth": "地",
    "Electric": "雷",
    "Electricity": "雷",
    "Fire": "火",
    "Grass": "草",
    "Ground": "地",
    "Ice": "冰",
    "Leaf": "草",
    "Neutral": "无",
    "Normal": "无",
    "Water": "水",
}

WORK_NAMES = {
    "kindling": "生火",
    "watering": "浇水",
    "planting": "播种",
    "generating_electricity": "发电",
    "handiwork": "手工作业",
    "gathering": "采集",
    "lumbering": "伐木",
    "mining": "采矿",
    "medicine_production": "制药",
    "cooling": "冷却",
    "transporting": "搬运",
    "farming": "牧场",
}

PALDB_ELEMENT_NAMES = {
    "Neutral": "无",
    "Fire": "火",
    "Water": "水",
    "Electric": "雷",
    "Grass": "草",
    "Ice": "冰",
    "Ground": "地",
    "Dark": "暗",
    "Dragon": "龙",
}

PALDB_WORK_NAMES = {
    "Kindling": "生火",
    "Watering": "浇水",
    "Planting": "播种",
    "Generating Electricity": "发电",
    "Handiwork": "手工作业",
    "Gathering": "采集",
    "Lumbering": "伐木",
    "Mining": "采矿",
    "Medicine Production": "制药",
    "Cooling": "冷却",
    "Transporting": "搬运",
    "Farming": "牧场",
}

PAL_ZH = {
    "Lamball": "棉悠悠",
    "Cattiva": "捣蛋猫",
    "Chikipi": "皮皮鸡",
    "Lifmunk": "翠叶鼠",
    "Foxparks": "火绒狐",
    "Fuack": "冲浪鸭",
    "Sparkit": "伏特喵",
    "Tanzee": "新叶猿",
    "Rooby": "燎火鹿",
    "Pengullet": "企丸丸",
}

ITEM_ZH = {
    "wool": "羊毛",
    "lamball_mutton": "棉悠悠羊肉",
    "red_berries": "红色野莓",
    "egg": "蛋",
    "chikipi_poultry": "皮皮鸡肉",
    "berry_seeds": "野莓种子",
    "low_grade_medical_supplies": "低品质药品",
    "leather": "皮革",
    "flame_organ": "喷火器官",
    "pal_fluids": "Pal Fluid",
    "ice_organ": "结冰器官",
    "electric_organ": "电气器官",
    "venom_gland": "毒腺",
    "bone": "骨头",
    "horn": "角",
    "high_quality_pal_oil": "优质帕鲁油",
    "beautiful_flower": "美丽花朵",
    "honey": "蜂蜜",
    "milk": "牛奶",
    "cotton_candy": "棉花糖",
    "coal": "煤炭",
    "pure_quartz": "纯水晶",
    "sulfur": "硫磺",
}


def title_from_slug(value):
    return value.replace("_", " ").replace("-", " ").title()


def item_name(value):
    return ITEM_ZH.get(value, title_from_slug(value))


def pal_label(pal):
    zh = PAL_ZH.get(pal["name"])
    return f"{pal['name']}（{zh}）" if zh else pal["name"]


def compact_work(suitability):
    if not suitability:
        return ""
    items = []
    for work in suitability:
        label = WORK_NAMES.get(work["type"], title_from_slug(work["type"]))
        items.append(f"{label} Lv{work['level']}")
    return "、".join(items)


def compact_types(types):
    return "、".join(TYPE_NAMES.get(t["name"], title_from_slug(t["name"])) for t in types)


def build_paldeck(pals):
    records = []
    for pal in pals:
        drops = "、".join(item_name(drop) for drop in pal.get("drops", []))
        aura = pal.get("aura") or {}
        breeding = pal.get("breeding") or {}
        records.append(
            {
                "number": pal["key"],
                "name": pal_label(pal),
                "elements": compact_types(pal.get("types", [])),
                "workSuitability": compact_work(pal.get("suitability", [])),
                "drops": drops,
                "partnerSkill": title_from_slug(aura.get("name", "")),
                "food": str((pal.get("stats") or {}).get("food", "")),
                "breedingRank": str(breeding.get("rank", "")),
                "wiki": pal.get("wiki", ""),
            }
        )

    return {
        "title": "帕鲁图鉴",
        "description": "速查全量帕鲁编号、属性、工作适性、掉落、伙伴技能、食量与繁殖排名。",
        "lastVerified": "2026-07-02",
        "columns": [
            {"key": "number", "label": "编号"},
            {"key": "name", "label": "名称"},
            {"key": "elements", "label": "属性"},
            {"key": "workSuitability", "label": "工作适性"},
            {"key": "drops", "label": "掉落"},
            {"key": "partnerSkill", "label": "伙伴技能"},
            {"key": "food", "label": "食量"},
            {"key": "breedingRank", "label": "繁殖排名"},
        ],
        "records": records,
        "sources": [
            {
                "label": "palworld-paldex-api (MIT)",
                "url": "https://github.com/mlg404/palworld-paldex-api",
            },
            {
                "label": "Palworld 官方页面",
                "url": "https://www.pocketpair.jp/en/games-en/palworld-en/",
            },
        ],
    }


def extract_thgl_paldeck_rows(html, detail_base_url):
    rows = []
    category = ""
    seen = set()
    pattern = re.compile(
        r'<div class="text-xs uppercase tracking-wider text-muted-foreground mb-1 px-1\.5">([^<]+)</div>'
        r'|<a class="flex items-center gap-2 [^"]*" href="/(?:zh-CN/)?db/paldeck/([^"]+)".*?'
        r'<span class="truncate text-sm">([^<]+)</span>',
        re.S,
    )
    for match in pattern.finditer(html):
        if match.group(1):
            category = unescape(match.group(1)).strip()
            continue
        pal_id = unescape(match.group(2)).strip()
        name = unescape(match.group(3)).strip()
        if pal_id and name and pal_id not in seen:
            seen.add(pal_id)
            rows.append(
                {
                    "id": pal_id,
                    "name": name,
                    "elementGroup": category,
                    "url": urljoin(detail_base_url + "/", pal_id),
                }
            )
    return rows


def load_thgl_paldeck_rows():
    raw_json = RAW_DIR / "palworld-thgl-paldeck.json"
    if raw_json.exists():
        return json.loads(raw_json.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        PALDECK_10_URL,
        headers={"User-Agent": "pal-database-data-builder/1.0 (+https://pal-database.pages.dev/)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    rows = extract_thgl_paldeck_rows(html, PALDECK_10_URL)
    raw_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def load_thgl_paldeck_en_rows():
    raw_json = RAW_DIR / "palworld-thgl-paldeck.en-US.json"
    if raw_json.exists():
        return json.loads(raw_json.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        PALDECK_10_EN_URL,
        headers={"User-Agent": "pal-database-data-builder/1.0 (+https://pal-database.pages.dev/)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    rows = extract_thgl_paldeck_rows(html, PALDECK_10_EN_URL)
    raw_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def extract_paldb_paldeck_rows(html):
    pattern = re.compile(
        r'<div class="col" data-filters="([^"]*)".*?'
        r'<img[^>]+src="([^"]*PalIcon/Normal/[^"]+)"[^>]*>.*?'
        r'<span class="text-white-50 small">#([^<]+)</span>\s*'
        r'<a class="itemname"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        re.S,
    )
    rows = []
    for match in pattern.finditer(html):
        filters, image, number, slug, english_name = (unescape(value).strip() for value in match.groups())
        tokens = filters.split()
        elements = [PALDB_ELEMENT_NAMES[token] for token in tokens if token in PALDB_ELEMENT_NAMES]
        work = []
        for source_name, chinese_name in PALDB_WORK_NAMES.items():
            work_match = re.search(rf"{re.escape(source_name)}([0-9]+)?\b", filters)
            if not work_match:
                continue
            level = work_match.group(1)
            work.append(f"{chinese_name} Lv{level}" if level else chinese_name)
        if number and english_name:
            rows.append(
                {
                    "number": number,
                    "englishName": english_name,
                    "image": image,
                    "elements": "、".join(elements),
                    "workSuitability": "、".join(work),
                    "url": urljoin(PALDB_EN_BASE_URL, slug),
                }
            )
    return rows


def load_paldb_paldeck_rows():
    raw_json = RAW_DIR / "paldb-pals.en-US.json"
    if raw_json.exists():
        rows = json.loads(raw_json.read_text(encoding="utf-8"))
        if rows and all(row.get("image") for row in rows):
            return rows

    request = urllib.request.Request(
        PALDB_PALS_URL,
        headers={"User-Agent": "pal-database-data-builder/1.0 (+https://pal-database.pages.dev/)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    rows = extract_paldb_paldeck_rows(html)
    raw_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def clean_html_text(value):
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = " ".join(unescape(value).replace("\xa0", " ").split())
    return "" if value in {"-", "—"} else value


def extract_paldb_detail(html):
    partner_match = re.search(
        r'<a href="Partner_Skill"[^>]*>.*?</a>\s*</div>\s*</div>\s*'
        r'<div style="border-left: solid white"><span class="ms-2">(.*?)</span>\s*Lv\.',
        html,
        re.S,
    )
    food_match = re.search(
        r"<div>进食量</div>\s*<div>(.*?)</div>\s*</div>",
        html,
        re.S,
    )
    drops_match = re.search(
        r'<h5[^>]*data-i18n="paldex_drop_item_title"[^>]*>.*?</h5>\s*'
        r'<table[^>]*>(.*?)</table>',
        html,
        re.S,
    )

    drops = []
    if drops_match:
        for item_html in re.findall(r'<a class="itemname"[^>]*>(.*?)</a>', drops_match.group(1), re.S):
            item_name = clean_html_text(item_html)
            if item_name and item_name not in drops:
                drops.append(item_name)

    return {
        "partnerSkill": clean_html_text(partner_match.group(1)) if partner_match else "",
        "food": str(food_match.group(1).count("T_Icon_foodamount_on.webp")) if food_match else "",
        "drops": "、".join(drops),
    }


def fetch_paldb_detail(row):
    slug = row["url"].rstrip("/").rsplit("/", 1)[-1]
    request = urllib.request.Request(
        urljoin(PALDB_CN_BASE_URL, slug),
        headers={"User-Agent": "pal-database-data-builder/1.0 (+https://pal-database.pages.dev/)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        detail = extract_paldb_detail(response.read().decode("utf-8"))
    return row["englishName"], detail


def load_paldb_paldeck_details(paldb_rows):
    raw_json = RAW_DIR / "paldb-pal-details.zh-CN.json"
    if raw_json.exists():
        return json.loads(raw_json.read_text(encoding="utf-8"))

    details = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_paldb_detail, row): row["englishName"] for row in paldb_rows}
        for future in as_completed(futures):
            english_name = futures[future]
            try:
                name, detail = future.result()
            except Exception as error:
                print(f"PalDB detail skipped for {english_name}: {error}")
                continue
            details[name] = detail

    raw_json.write_text(json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return details


def build_paldeck_10(rows, english_rows, paldb_rows, paldb_details):
    english_by_id = {row["id"]: row["name"] for row in english_rows}
    paldb_by_name = {row["englishName"]: row for row in paldb_rows}
    records = []
    for row in rows:
        english_name = row.get("englishName", english_by_id.get(row["id"], ""))
        paldb_row = paldb_by_name.get(english_name, {})
        paldb_detail = paldb_details.get(english_name, {})
        records.append(
            {
                "number": paldb_row.get("number", ""),
                "image": paldb_row.get("image", ""),
                "name": row["name"],
                "elements": paldb_row.get("elements")
                or THGL_ELEMENT_NAMES.get(row.get("elementGroup"), row.get("elementGroup", "")),
                "workSuitability": paldb_row.get("workSuitability") or "资料源未列出",
                "partnerSkill": paldb_detail.get("partnerSkill") or "资料源未列出",
                "drops": paldb_detail.get("drops") or "资料源未列出",
                "food": paldb_detail.get("food") or "资料源未列出",
                "id": row["id"],
                "detail": row.get("detail", row.get("url", "")),
            }
        )
    records.sort(key=lambda record: (paldeck_number_key(record["number"]), record["name"]))
    return {
        "title": "1.0 帕鲁图鉴",
        "description": "按公开 Paldeck 列表与交叉核验资料整理编号、中文名、元素、工作适性、伙伴技能、掉落与进食量。",
        "lastVerified": "2026-07-13",
        "columns": [
            {"key": "number", "label": "编号"},
            {"key": "image", "label": "图像"},
            {"key": "name", "label": "名称"},
            {"key": "elements", "label": "元素"},
            {"key": "workSuitability", "label": "工作适性"},
            {"key": "partnerSkill", "label": "伙伴技能"},
            {"key": "drops", "label": "可能掉落"},
            {"key": "food", "label": "进食量"},
            {"key": "id", "label": "Paldeck ID"},
            {"key": "detail", "label": "详情"},
        ],
        "records": records,
        "sources": [
            {
                "label": "TH.GL Palworld Paldeck",
                "url": PALDECK_10_URL,
            },
            {
                "label": "Palworld v1.0 官方更新日志",
                "url": "https://store.steampowered.com/news/app/1623730/view/686383649529010623?l=schinese",
            },
            {
                "label": "palworld-paldex-api (MIT)",
                "url": "https://github.com/mlg404/palworld-paldex-api",
            },
            {
                "label": "PalDB Pals（编号、元素、工作适性、伙伴技能、掉落、进食量）",
                "url": PALDB_PALS_URL,
            },
            {
                "label": "Palworld.gg cross-check",
                "url": "https://palworld.gg/pals",
            },
        ],
    }


def load_paldeck_10_supplements():
    if not PALDECK_10_SUPPLEMENTS.exists():
        return []
    return json.loads(PALDECK_10_SUPPLEMENTS.read_text(encoding="utf-8"))


def merge_paldeck_10_rows(rows, supplements):
    merged = list(rows)
    seen = {row["id"] for row in rows}
    for row in supplements:
        if row["id"] not in seen:
            merged.append(row)
            seen.add(row["id"])
    return merged


def paldeck_number_key(value):
    match = re.fullmatch(r"(\d+)([A-Z]?)", value)
    if match:
        return int(match.group(1)), match.group(2)
    return 10_000, value


def build_materials(rows, english_rows, paldb_rows, paldb_details):
    english_by_id = {row["id"]: row["name"] for row in english_rows}
    number_by_name = {row["englishName"]: row["number"] for row in paldb_rows}
    by_drop = {}
    for row in rows:
        english_name = row.get("englishName", english_by_id.get(row["id"], ""))
        number = number_by_name.get(english_name, "")
        drops = paldb_details.get(english_name, {}).get("drops", "")
        for drop in filter(None, drops.split("、")):
            by_drop.setdefault(drop, []).append((number, row["name"]))

    records = []
    for drop, sources in sorted(by_drop.items()):
        source_labels = []
        for number, name in sorted(sources, key=lambda item: (paldeck_number_key(item[0]), item[1])):
            label = f"#{number} {name}" if number else name
            if label not in source_labels:
                source_labels.append(label)
        records.append(
            {
                "name": drop,
                "sourceType": "帕鲁掉落",
                "source": "、".join(source_labels),
                "sourceCount": str(len(source_labels)),
            }
        )

    return {
        "title": "1.0 材料掉落",
        "description": "按 1.0 图鉴的可能掉落反查来源帕鲁；可用材料名或帕鲁名筛选。",
        "lastVerified": "2026-07-13",
        "columns": [
            {"key": "name", "label": "材料"},
            {"key": "sourceType", "label": "来源类型"},
            {"key": "source", "label": "来源帕鲁"},
            {"key": "sourceCount", "label": "来源数量"},
        ],
        "records": records,
        "sources": [
            {
                "label": "PalDB 中文帕鲁详情（可能掉落）",
                "url": "https://paldb.cc/cn/Pals",
            },
            {
                "label": "TH.GL Palworld Paldeck（中文名、ID）",
                "url": PALDECK_10_URL,
            }
        ],
    }


def build_breeding(pals, breeding, paldeck_records, english_by_id):
    pal_by_key = {pal["key"]: pal for pal in pals}
    paldeck_by_english_name = {
        english_by_id.get(record["id"]): record
        for record in paldeck_records
        if english_by_id.get(record["id"])
    }

    def display_pal(key):
        source_pal = pal_by_key.get(key)
        if not source_pal:
            return None
        record = paldeck_by_english_name.get(source_pal["name"])
        if not record or not record.get("name") or not record.get("image"):
            return None
        return {
            "key": key,
            "number": record["number"],
            "name": record["name"],
            "image": record["image"],
        }

    visible_pals = {key: display_pal(key) for key in pal_by_key}
    pal_options = sorted(
        (pal for pal in visible_pals.values() if pal),
        key=lambda pal: (paldeck_number_key(pal["number"]), pal["name"]),
    )

    pairs = []
    for child_key, parent_pairs in breeding.items():
        child = visible_pals.get(child_key)
        if not child:
            continue
        for parent_a, parent_b in parent_pairs:
            a = visible_pals.get(parent_a)
            b = visible_pals.get(parent_b)
            if not a or not b:
                continue
            pairs.append(
                {
                    "parentA": parent_a,
                    "parentB": parent_b,
                    "child": child_key,
                    "parentAInfo": a,
                    "parentBInfo": b,
                    "childInfo": child,
                }
            )

    return {
        "title": "配种数据",
        "description": "仅显示已映射到当前中文图鉴的配种组合，可按父母或目标子代查询。",
        "lastVerified": "2026-07-02",
        "pals": pal_options,
        "pairs": pairs,
        "sources": [
            {
                "label": "palworld-paldex-api (MIT)",
                "url": "https://github.com/mlg404/palworld-paldex-api",
            }
        ],
    }


def categorize_technology(tech_id):
    if tech_id.startswith("SkillUnlock_"):
        return "伙伴装备"
    if "Armor" in tech_id or "Helm" in tech_id or "Shield" in tech_id:
        return "防具"
    if "RangeWeapon" in tech_id or "MeleeWeapon" in tech_id or "Bullet" in tech_id or "Arrow" in tech_id:
        return "武器弹药"
    if tech_id.startswith("Product_") or "Factory" in tech_id or "Workbench" in tech_id:
        return "生产设施"
    if "Farm" in tech_id or "PalBed" in tech_id or "PalFoodBox" in tech_id or "Spa" in tech_id:
        return "据点设施"
    if "Sphere" in tech_id:
        return "帕鲁球"
    if "Glider" in tech_id or "Lantern" in tech_id or "Pouch" in tech_id or "Accessory" in tech_id:
        return "探索辅助"
    return "科技"


def extract_technology_rows(html):
    rows = []
    pattern = re.compile(r"<tr><td>(.*?)</td><td>(.*?)</td></tr>")
    for tech_id, name in pattern.findall(html):
        tech_id = unescape(re.sub(r"<.*?>", "", tech_id)).strip()
        name = unescape(re.sub(r"<.*?>", "", name)).strip()
        if tech_id and name and tech_id != "Technology ID":
            rows.append({"id": tech_id, "name": name})
    return rows


def load_technology_rows():
    raw_json = RAW_DIR / "palworld-technologyids.json"
    if raw_json.exists():
        return json.loads(raw_json.read_text(encoding="utf-8"))

    html_path = RAW_DIR / "palworld-technologyids.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(TECH_URL, timeout=30) as response:
            html = response.read().decode("utf-8")

    rows = extract_technology_rows(html)
    raw_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def build_technology(rows):
    records = [
        {
            "id": row["id"],
            "name": row["name"],
            "category": categorize_technology(row["id"]),
            "source": "Palworld Server Guide",
        }
        for row in rows
    ]
    return {
        "title": "科技树",
        "description": "按官方 Technology ID 速查科技、伙伴装备、设施、武器弹药和探索辅助项目。",
        "lastVerified": "2026-07-02",
        "columns": [
            {"key": "id", "label": "Technology ID"},
            {"key": "name", "label": "科技名称"},
            {"key": "category", "label": "分类"},
            {"key": "source", "label": "来源"},
        ],
        "records": records,
        "sources": [
            {
                "label": "Palworld Server Guide - Technology IDs",
                "url": TECH_URL,
            }
        ],
    }


RECIPE_CATEGORY_NAMES = {
    "Accessory": "饰品",
    "Ammo": "弹药",
    "Armor": "防具",
    "Blueprint": "设计图",
    "CaptureItemModifier": "捕获组件",
    "Consume": "消耗品",
    "Essential": "关键物品",
    "Food": "食物",
    "Glider": "滑翔装备",
    "Material": "材料",
    "SpecialWeapon": "特殊道具",
    "Weapon": "武器",
}


def extract_recipe_rows(html):
    rows = []
    category = ""
    pattern = re.compile(
        r'<div class="text-xs uppercase tracking-wider text-muted-foreground mb-1 px-1\.5">([^<]+)</div>'
        r'|<a class="flex items-center gap-2 [^"]*" href="/zh-CN/db/recipes/([^"]+)".*?'
        r'<span class="truncate text-sm">([^<]+)</span>',
        re.S,
    )
    for match in pattern.finditer(html):
        if match.group(1):
            category = unescape(match.group(1)).strip()
            continue
        recipe_id = unescape(match.group(2)).strip()
        name = unescape(match.group(3)).strip()
        if recipe_id and name:
            rows.append(
                {
                    "id": recipe_id,
                    "name": name,
                    "category": category,
                    "url": urljoin(RECIPES_URL + "/", recipe_id),
                }
            )
    return rows


def load_recipe_rows():
    raw_json = RAW_DIR / "palworld-thgl-recipes.json"
    if raw_json.exists():
        return json.loads(raw_json.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        RECIPES_URL,
        headers={"User-Agent": "pal-database-data-builder/1.0 (+https://pal-database.pages.dev/)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    rows = extract_recipe_rows(html)
    raw_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def build_recipes(rows):
    records = [
        {
            "id": row["id"],
            "name": row["name"],
            "category": RECIPE_CATEGORY_NAMES.get(row.get("category"), row.get("category", "")),
            "source": "TH.GL Palworld Database",
            "detail": row["url"],
        }
        for row in rows
    ]
    return {
        "title": "制作配方",
        "description": "按公开配方列表整理制作项 ID、名称、分类与来源详情页，适合检索制作链入口。",
        "lastVerified": "2026-07-02",
        "columns": [
            {"key": "id", "label": "配方 ID"},
            {"key": "name", "label": "配方名称"},
            {"key": "category", "label": "分类"},
            {"key": "source", "label": "来源"},
            {"key": "detail", "label": "详情"},
        ],
        "records": records,
        "sources": [
            {
                "label": "TH.GL Palworld Recipes",
                "url": RECIPES_URL,
            }
        ],
    }


def main():
    pals = json.loads((RAW_DIR / "paldex-api-pals.json").read_text(encoding="utf-8"))
    breeding = json.loads((RAW_DIR / "paldex-api-breeding.json").read_text(encoding="utf-8"))
    technology_rows = load_technology_rows()
    recipe_rows = load_recipe_rows()
    paldeck_10_supplements = load_paldeck_10_supplements()
    paldeck_10_rows = load_thgl_paldeck_rows()
    paldeck_10_rows = merge_paldeck_10_rows(paldeck_10_rows, paldeck_10_supplements)
    paldeck_10_english_rows = load_thgl_paldeck_en_rows()
    paldb_paldeck_rows = load_paldb_paldeck_rows()
    paldb_paldeck_details = load_paldb_paldeck_details(paldb_paldeck_rows)

    paldeck_10_data = build_paldeck_10(
        paldeck_10_rows,
        paldeck_10_english_rows,
        paldb_paldeck_rows,
        paldb_paldeck_details,
    )
    paldeck_10_english_by_id = {row["id"]: row["name"] for row in paldeck_10_english_rows}
    paldeck_10_english_by_id.update(
        {row["id"]: row["englishName"] for row in paldeck_10_supplements if row.get("englishName")}
    )

    outputs = {
        "paldeck.zh-CN.json": build_paldeck(pals),
        "paldeck-1.0.zh-CN.json": paldeck_10_data,
        "materials.zh-CN.json": build_materials(
            paldeck_10_rows,
            paldeck_10_english_rows,
            paldb_paldeck_rows,
            paldb_paldeck_details,
        ),
        "breeding.zh-CN.json": build_breeding(
            pals,
            breeding,
            paldeck_10_data["records"],
            paldeck_10_english_by_id,
        ),
        "technology.zh-CN.json": build_technology(technology_rows),
        "recipes.zh-CN.json": build_recipes(recipe_rows),
    }

    for filename, data in outputs.items():
        (OUT_DIR / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record_count = len(data.get("records", data.get("pairs", [])))
        print(f"{filename}: {record_count} records")


if __name__ == "__main__":
    main()
