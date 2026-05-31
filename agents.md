# StellectList 清单生成指南

## 项目结构

```
StellectList/
├── indexes.json              # 根索引，汇总所有分类
├── deploy.py                 # 校验 & 部署脚本
├── lists/                    # 正式清单目录
│   ├── city/
│   │   ├── _indexes.json     # 分类索引（自动生成，_ 前缀）
│   │   └── cities_china.json
│   ├── food/
│   ├── hiking/
│   ├── life/
│   └── movie/
└── tmps/                     # 待校验/校验失败的清单
```

## 现有分类

| id | 示例清单 |
|------|------|
| city | 中国最美的50座城市 |
| food | 此生必吃的100样美食 |
| hiking | 北京周边值得爬的50座山 |
| life | 一辈子要完成的100件事 |
| movie | 一生必看的100部电影 |

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

### 顶层字段（全部必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 清单唯一标识，建议用英文小写+下划线 |
| name | string | 清单名称 |
| desc | string | 清单简短描述（可为空字符串） |
| icon | string | SF Symbol 名称或 emoji 表情符号 |
| category | string | 所属分类 id |
| date | string | 创建日期，格式 YYYY-MM-DD |
| items | array | 清单条目，不能为空 |

### items 条目字段

| 字段 | 是否必填 | 类型 | 说明 |
|------|---------|------|------|
| name | 必填 | string | 条目名称 |
| desc | 可选（建议带上） | string | 条目描述 |
| latitude | 可选 | number | 纬度 |
| longitude | 可选 | number | 经度 |
| address | 可选 | string | 地址信息 |

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
- 校验完成后自动生成根 `indexes.json` 和每个分类的 `_indexes.json`

## 注意事项

- icon 推荐使用 Apple SF Symbols（如 `building.2.fill`、`fork.knife`、`figure.hiking`），也可以直接用 emoji
- 每个清单的 items 数量建议 20-100 个
- 有地理位置属性的条目建议补全 latitude、longitude、address
- 生成清单时 date 填当天日期
