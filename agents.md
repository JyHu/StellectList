# StellectList 清单生成指南

## 项目结构

```
StellectList/
├── indexes.json              # 根索引（自动生成，勿手动编辑）
├── deploy.py                 # 校验 & 部署脚本
├── lists/                    # 正式清单目录
│   ├── city/
│   │   ├── _indexes.json     # 分类索引（自动生成，_ 前缀）
│   │   ├── cities_china.json
│   │   └── romantic_cities_50.json
│   ├── book/
│   ├── culture/
│   ├── food/
│   ├── hiking/
│   ├── life/
│   ├── movie/
│   ├── music/
│   ├── nature/
│   ├── sport/
│   └── travel/
└── tmps/                     # 待校验/校验失败的清单
```

## 现有分类

| id | name | icon | 清单数 |
|------|------|------|--------|
| book | 阅读 | book.fill | 2 |
| city | 城市 | building.2.fill | 2 |
| culture | 文化 | building.columns.fill | 2 |
| food | 美食 | fork.knife | 3 |
| hiking | 徒步 | figure.hiking | 3 |
| life | 人生 | heart.fill | 2 |
| movie | 电影 | film.fill | 2 |
| music | 音乐 | music.note | 2 |
| nature | 自然 | leaf.fill | 3 |
| sport | 运动 | sportscourt.fill | 1 |
| travel | 旅行 | airplane | 4 |

## 工作流程

1. **生成清单** → 放到 `tmps/` 目录下
2. **如果是新分类** → 在 `lists/` 下新建对应目录，并创建 `_indexes.json` 填写分类信息（name、icon、desc）
3. **运行部署** → 执行 `python3 deploy.py`，脚本会自动校验、归档、生成索引

> 根目录下的 `indexes.json` 完全由脚本从 `lists/*/_indexes.json` 自动生成，**不要手动编辑**。

## 清单文件结构

每个清单必须是一个 JSON 文件，结构如下：

```json
{
  "id": "cities_china",
  "name": "中国最美的50座城市",
  "desc": "总有一座城市让你念念不忘",
  "icon": "building.2.fill",
  "category": "city",
  "date": "2026-05-31",
  "items": [
    {"name": "杭州", "desc": "人间天堂，西湖美景", "latitude": 30.2741, "longitude": 120.1551, "address": "浙江省杭州市"},
    {"name": "苏州", "desc": "上有天堂下有苏杭", "latitude": 31.2990, "longitude": 120.5853, "address": "江苏省苏州市"}
  ]
}
```

> deploy 脚本会自动将 `date` 转为秒级时间戳，并添加 `count` 字段。

### 顶层字段（全部必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 清单唯一标识，建议用英文小写+下划线 |
| name | string | 清单名称 |
| desc | string | 清单简短描述（可为空字符串） |
| icon | string | SF Symbol 名称或 emoji 表情符号 |
| category | string | 所属分类 id |
| date | string/number | 创建日期，格式 YYYY-MM-DD 或秒级时间戳 |
| items | array | 清单条目，不能为空 |

### 自动生成字段（deploy 脚本维护）

| 字段 | 类型 | 说明 |
|------|------|------|
| count | number | items 条目数量，由脚本自动写入 |
| date | number | 部署后会被转换为秒级时间戳 |

### items 条目字段

| 字段 | 是否必填 | 类型 | 说明 |
|------|---------|------|------|
| name | 必填 | string | 条目名称 |
| desc | 可选（建议带上） | string | 条目描述 |
| latitude | 可选 | number | 纬度 |
| longitude | 可选 | number | 经度 |
| address | 可选 | string | 地址信息 |

## 索引文件结构

### 根索引 indexes.json（自动生成）

```json
{
  "updateAt": 1780215741,
  "categories": [
    {"id": "city", "name": "城市", "icon": "building.2.fill", "desc": "探索世界上最美的城市", "count": 2, "updateAt": 1780156800}
  ]
}
```

- `updateAt`（根级）：脚本运行时的秒级时间戳
- `categories`：数组，按各分类的 `updateAt` 降序排列（最近更新的排前面）
- 每个分类的 `updateAt`：该分类下最新清单的 date

### 分类索引 _indexes.json（自动生成）

```json
{
  "id": "city",
  "name": "城市",
  "icon": "building.2.fill",
  "desc": "探索世界上最美的城市",
  "count": 2,
  "updateAt": 1780156800,
  "items": [
    {"id": "cities_china", "name": "中国最美的50座城市", "desc": "总有一座城市让你念念不忘", "icon": "building.2.fill", "date": 1780156800, "count": 50}
  ]
}
```

- `count`：该分类下清单文件数量
- `updateAt`：该分类下最新清单的 date 时间戳
- `items`：按 date 降序排列，同日期按名称字母序
- `name`、`icon`、`desc` 需在新建分类时手动填写，脚本会保留

## 命名规范

- 文件名：英文小写 + 下划线，如 `cities_china.json`、`food_100.json`
- **内容文件不允许以 `_` 开头**（`_` 前缀保留给系统索引文件如 `_indexes.json`）
- id 字段：与文件名一致（不含 .json 后缀）
- category：使用已有分类 id，新分类需在 `lists/` 下新建目录并创建 `_indexes.json`

## deploy.py 校验规则

- 递归扫描 `lists/` 和 `tmps/` 下所有 JSON 文件（跳过 `_` 前缀的索引文件）
- 内容文件名不允许以 `_` 开头（否则校验失败）
- 校验通过 → 移动到 `lists/<category>/`
- 校验失败 → 移动到 `tmps/`，输出具体错误原因
- 校验完成后：
  - 每个清单文件写入 `count`，`date` 转为秒级时间戳
  - 生成每个分类的 `_indexes.json`（含 `updateAt`）
  - 生成根 `indexes.json`（按 `updateAt` 排序）

## 注意事项

- icon 推荐使用 Apple SF Symbols（如 `building.2.fill`、`fork.knife`、`figure.hiking`），也可以直接用 emoji
- 每个清单的 items 数量建议 20-100 个
- 有地理位置属性的条目建议补全 latitude、longitude、address
- 生成清单时 date 填当天日期（YYYY-MM-DD 格式即可，脚本会自动转换）
- 所有时间戳均为秒级（10位数字）
