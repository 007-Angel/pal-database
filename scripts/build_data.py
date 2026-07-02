import json
import re
import urllib.request
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TECH_URL = "https://docs.palworldgame.com/settings-and-operation/technologyids/"


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


def build_materials(pals):
    by_drop = {}
    for pal in pals:
        for drop in pal.get("drops", []):
            by_drop.setdefault(drop, []).append(pal_label(pal))

    records = []
    for drop, sources in sorted(by_drop.items(), key=lambda item: item_name(item[0])):
        records.append(
            {
                "name": item_name(drop),
                "sourceType": "帕鲁掉落",
                "source": "、".join(sources[:12]),
                "sourceCount": str(len(sources)),
                "usage": "按制作配方和科技需求使用",
                "route": "从掉落帕鲁反查获取来源",
            }
        )

    return {
        "title": "材料掉落",
        "description": "按掉落物反查来源帕鲁，适合查找材料获取对象。",
        "lastVerified": "2026-07-02",
        "columns": [
            {"key": "name", "label": "材料"},
            {"key": "sourceType", "label": "来源类型"},
            {"key": "source", "label": "来源帕鲁"},
            {"key": "sourceCount", "label": "来源数量"},
            {"key": "usage", "label": "主要用途"},
            {"key": "route", "label": "获取方式"},
        ],
        "records": records,
        "sources": [
            {
                "label": "palworld-paldex-api (MIT)",
                "url": "https://github.com/mlg404/palworld-paldex-api",
            }
        ],
    }


def build_breeding(pals, breeding):
    pal_by_key = {pal["key"]: pal for pal in pals}
    pal_options = [
        {
            "key": pal["key"],
            "name": pal_label(pal),
            "elements": compact_types(pal.get("types", [])),
            "rank": (pal.get("breeding") or {}).get("rank"),
        }
        for pal in pals
    ]

    pairs = []
    for child_key, parent_pairs in breeding.items():
        child = pal_by_key.get(child_key)
        if not child:
            continue
        for parent_a, parent_b in parent_pairs:
            a = pal_by_key.get(parent_a)
            b = pal_by_key.get(parent_b)
            if not a or not b:
                continue
            pairs.append(
                {
                    "parentA": parent_a,
                    "parentB": parent_b,
                    "parentALabel": pal_label(a),
                    "parentBLabel": pal_label(b),
                    "child": child_key,
                    "childLabel": pal_label(child),
                }
            )

    return {
        "title": "配种数据",
        "description": "按父母组合查询子代，或按目标子代反查父母组合。",
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


def main():
    pals = json.loads((RAW_DIR / "paldex-api-pals.json").read_text(encoding="utf-8"))
    breeding = json.loads((RAW_DIR / "paldex-api-breeding.json").read_text(encoding="utf-8"))
    technology_rows = load_technology_rows()

    outputs = {
        "paldeck.zh-CN.json": build_paldeck(pals),
        "materials.zh-CN.json": build_materials(pals),
        "breeding.zh-CN.json": build_breeding(pals, breeding),
        "technology.zh-CN.json": build_technology(technology_rows),
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
