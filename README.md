# 帕鲁资料站

这是一个静态首版骨架，用于搭建独立的中文帕鲁资料库，后续可以接入“五彩缤纷”作为游戏资料站入口。

## 当前范围

- 首页、左侧导航、搜索入口、模块卡片
- 帕鲁图鉴、科技树、材料掉落、版本更新的数据工作台
- 配种计算、据点建造、地图探索、新手路线的功能框架页
- 关于本站、非官方声明、隐私政策、404、robots、sitemap、favicon、manifest
- 中文优先，`en/` 与 `data/site.en-US.json` 已预留
- 非官方免责声明与 Pocketpair 二创指南链接

## 资料数据

核心资料先放在 `data/` 目录，页面会通过 `assets/database.js` 自动读取并渲染。

```text
data/paldeck.zh-CN.json      帕鲁图鉴字段与记录
data/materials.zh-CN.json    材料掉落字段与记录
data/technology.zh-CN.json   科技树字段与记录
data/updates.zh-CN.json      版本更新字段与记录
data/planning.zh-CN.json     站点建设路线
```

新增记录时，优先补 `records` 数组，并保留 `verified` 或 `lastVerified` 字段。没有核验过的资料不要直接当成事实写入。

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

`assets/hero-pal-database.png` 是为本站生成的原创横幅图，不使用官方 Logo，不复刻官方帕鲁形象。后续如果要使用官方截图或素材，建议继续保留“非官方”标识，并按 Pocketpair 二创指南控制使用方式。
