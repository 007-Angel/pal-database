# 帕鲁资料站

这是一个静态中文帕鲁资料库，可以接入“五彩缤纷”作为游戏资料站入口。

## 当前范围

- 首页、左侧导航、搜索入口、模块卡片
- 帕鲁图鉴、科技树、材料掉落、版本更新的数据工作台
- 配种计算、据点建造、地图探索、新手路线的资料页
- 关于本站、非官方声明、隐私政策、404、robots、sitemap、favicon、manifest
- 中文优先，`en/` 与 `data/site.en-US.json` 用于英文版入口
- 非官方免责声明与 Pocketpair 二创指南链接

## 资料数据

核心资料放在 `data/` 目录，页面会通过 `assets/database.js` 自动读取并渲染。

```text
data/generated/              由脚本生成的图鉴索引、材料、科技、配方和配种数据
data/updates.zh-CN.json      版本更新字段与记录
data/map.zh-CN.json          1.0 地图变化字段与记录
data/guides.zh-CN.json       1.0 开荒与回归路线字段与记录
data/release-1.0.zh-CN.json  1.0 正式版总览字段与记录
data/raw/                    第三方 MIT 数据源缓存
```

图鉴、材料、科技、配方、配种以 `data/generated/` 为主；版本更新等人工摘要保存在独立 JSON。没有核验过的资料不要直接当成事实写入。

生成全量资料：

```powershell
python scripts\build_data.py
```

## 发布方式

直接发布整个目录即可。Cloudflare Pages 设置如下：

```text
Framework preset: None
Build command: exit 0
Build output directory: .
```

本地预览可以直接打开 `index.html`，也可以在目录中运行：

```powershell
python -m http.server 4173
```

然后访问 `http://localhost:4173/`。

## 素材说明

`assets/hero-pal-database.png` 是为本站生成的原创横幅图，不使用官方 Logo，不复刻官方帕鲁形象。引用官方截图或素材时，建议继续保留“非官方”标识，并按 Pocketpair 二创指南控制使用方式。

## 第三方数据

原有图鉴明细、材料和配种底座来自 `mlg404/palworld-paldex-api` 的 MIT 授权数据，并转换为本站字段。1.0 图鉴索引与配方索引来自 TH.GL 的公开列表。科技索引来自 Palworld Server Guide 的 Technology IDs 页面。1.0 正式版、地图和攻略摘要来自官方 Steam 更新日志。授权与来源说明见 `THIRD_PARTY_NOTICES.md` 与 `data/raw/paldex-api-LICENSE.txt`。
