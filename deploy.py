#!/usr/bin/env python3
"""
Deploy script for StellectList.
Validates JSON files in lists/ and tmps/ directories,
moves valid files to lists/<category>/, invalid files to tmps/,
and generates indexes.
"""

import json
import shutil
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent
LISTS_DIR = ROOT_DIR / "lists"
TMPS_DIR = ROOT_DIR / "tmps"
ROOT_INDEX = ROOT_DIR / "indexes.json"

REQUIRED_FIELDS = {"id", "name", "desc", "icon", "category", "date", "items"}
REQUIRED_ITEM_FIELDS = {"name"}
OPTIONAL_ITEM_FIELDS = {"desc", "address", "latitude", "longitude"}
CATEGORY_INDEX_NAME = "_indexes.json"


def load_category_index(category_dir):
    """Load _indexes.json from a category directory."""
    cat_index_file = category_dir / CATEGORY_INDEX_NAME
    if not cat_index_file.exists():
        return {}
    try:
        with open(cat_index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return {}


def validate_item(item, index):
    """Validate a single item in the items array."""
    errors = []
    if not isinstance(item, dict):
        errors.append(f"  items[{index}]: not a valid object")
        return errors

    for field in REQUIRED_ITEM_FIELDS:
        if field not in item:
            errors.append(f"  items[{index}]: missing required field '{field}'")
        elif not isinstance(item[field], str) or not item[field].strip():
            errors.append(f"  items[{index}]: field '{field}' must be a non-empty string")

    if "latitude" in item:
        if not isinstance(item["latitude"], (int, float)):
            errors.append(f"  items[{index}]: 'latitude' must be a number")
    if "longitude" in item:
        if not isinstance(item["longitude"], (int, float)):
            errors.append(f"  items[{index}]: 'longitude' must be a number")

    # Check for unexpected fields
    allowed = REQUIRED_ITEM_FIELDS | OPTIONAL_ITEM_FIELDS
    for key in item:
        if key not in allowed:
            errors.append(f"  items[{index}]: unexpected field '{key}'")

    return errors


def validate_json_file(filepath):
    """Validate a JSON file against the schema. Returns (data, errors)."""
    errors = []

    # Content files must not start with underscore
    if filepath.name.startswith("_"):
        return None, [f"File name must not start with '_' (reserved for index files)"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, [f"Invalid JSON: {e}"]
    except Exception as e:
        return None, [f"Cannot read file: {e}"]

    if not isinstance(data, dict):
        return None, ["Root must be a JSON object"]

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field '{field}'")

    # Validate field types
    if "id" in data and (not isinstance(data["id"], str) or not data["id"].strip()):
        errors.append("'id' must be a non-empty string")
    if "name" in data and (not isinstance(data["name"], str) or not data["name"].strip()):
        errors.append("'name' must be a non-empty string")
    if "desc" in data and (not isinstance(data["desc"], str)):
        errors.append("'desc' must be a string")
    if "icon" in data and (not isinstance(data["icon"], str) or not data["icon"].strip()):
        errors.append("'icon' must be a non-empty string")
    if "category" in data and (not isinstance(data["category"], str) or not data["category"].strip()):
        errors.append("'category' must be a non-empty string")
    if "date" in data and (not isinstance(data["date"], str) or not data["date"].strip()):
        errors.append("'date' must be a non-empty string")

    # Validate items
    if "items" in data:
        if not isinstance(data["items"], list):
            errors.append("'items' must be an array")
        elif len(data["items"]) == 0:
            errors.append("'items' must not be empty")
        else:
            for i, item in enumerate(data["items"]):
                errors.extend(validate_item(item, i))

    return data, errors


def move_to_tmps(filepath):
    """Move a file to the tmps directory."""
    TMPS_DIR.mkdir(parents=True, exist_ok=True)
    dest = TMPS_DIR / filepath.name
    if dest == filepath:
        return
    shutil.move(str(filepath), str(dest))


def move_to_category(filepath, category):
    """Move a file to lists/<category>/ directory."""
    category_dir = LISTS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    dest = category_dir / filepath.name
    if dest == filepath:
        return
    shutil.move(str(filepath), str(dest))


def collect_json_files():
    """Recursively collect all JSON files from lists/ and tmps/ (excluding _indexes.json)."""
    files = []
    for directory in [LISTS_DIR, TMPS_DIR]:
        if not directory.exists():
            continue
        for filepath in directory.rglob("*.json"):
            if filepath.name == CATEGORY_INDEX_NAME:
                continue
            files.append(filepath)
    return files


def update_list_count(filepath):
    """Update the count field in a list JSON file to match its items length."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["count"] = len(data.get("items", []))
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def generate_category_index(category_dir):
    """Generate _indexes.json for a specific category directory."""
    category = category_dir.name
    items = []
    file_count = 0

    for filepath in sorted(category_dir.glob("*.json")):
        if filepath.name.startswith("_"):
            continue
        file_count += 1
        try:
            # Update count in each list file
            update_list_count(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            items.append({
                "id": data["id"],
                "name": data["name"],
                "desc": data["desc"],
                "icon": data.get("icon", ""),
                "date": data.get("date", ""),
                "count": data.get("count", 0),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort: newest date first, then by name alphabetically for same date
    items.sort(key=lambda x: (-_date_sort_key(x.get("date", "")), x.get("name", "")))

    # Read existing _indexes.json to preserve category metadata (name/icon/desc)
    cat_index_file = category_dir / CATEGORY_INDEX_NAME
    old_data = load_category_index(category_dir)
    cat_name = old_data.get("name", "")
    cat_icon = old_data.get("icon", "")
    cat_desc = old_data.get("desc", "")

    index_data = {
        "id": category,
        "name": cat_name,
        "icon": cat_icon,
        "desc": cat_desc,
        "count": file_count,
        "items": items,
    }

    with open(cat_index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=4)

    return file_count


def _date_sort_key(date_str):
    """Convert date string to sortable integer. Returns 0 for invalid dates."""
    try:
        parts = date_str.split("-")
        return int(parts[0]) * 10000 + int(parts[1]) * 100 + int(parts[2])
    except (IndexError, ValueError):
        return 0


def generate_root_index():
    """Generate the root indexes.json purely from lists/*/_indexes.json."""
    categories = {}
    warnings = []

    if not LISTS_DIR.exists():
        return warnings

    for category_dir in sorted(LISTS_DIR.iterdir()):
        if not category_dir.is_dir():
            continue

        category = category_dir.name

        # Read category metadata solely from _indexes.json
        cat_data = load_category_index(category_dir)
        if not cat_data:
            continue

        cat_name = cat_data.get("name", "")
        cat_icon = cat_data.get("icon", "")
        cat_desc = cat_data.get("desc", "")
        cat_count = cat_data.get("count", 0)

        if cat_count == 0:
            continue

        if not cat_name:
            warnings.append(f"Warning: category '{category}' missing 'name', please update lists/{category}/{CATEGORY_INDEX_NAME}")
        if not cat_icon:
            warnings.append(f"Warning: category '{category}' missing 'icon', please update lists/{category}/{CATEGORY_INDEX_NAME}")

        categories[category] = [{
            "id": category,
            "name": cat_name,
            "icon": cat_icon,
            "desc": cat_desc,
            "count": cat_count,
        }]

    root_data = {
        "updateAt": int(time.time() * 1000),
        "categories": categories,
    }
    with open(ROOT_INDEX, "w", encoding="utf-8") as f:
        json.dump(root_data, f, ensure_ascii=False, indent=4)

    return warnings


def main():
    print("=" * 50)
    print("StellectList Deploy Script")
    print("=" * 50)

    # Ensure directories exist
    LISTS_DIR.mkdir(parents=True, exist_ok=True)
    TMPS_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all JSON files
    json_files = collect_json_files()

    if not json_files:
        print("\nNo JSON files found to process.")
    else:
        print(f"\nFound {len(json_files)} JSON file(s) to validate.\n")

    valid_count = 0
    invalid_count = 0

    for filepath in json_files:
        rel_path = filepath.relative_to(ROOT_DIR)
        data, errors = validate_json_file(filepath)

        if errors:
            invalid_count += 1
            print(f"FAIL: {rel_path}")
            for err in errors:
                print(f"  {err}")
            move_to_tmps(filepath)
        else:
            valid_count += 1
            category = data["category"]
            print(f"  OK: {rel_path} -> lists/{category}/")
            move_to_category(filepath, category)

    # Clean up empty directories in lists/
    if LISTS_DIR.exists():
        for d in list(LISTS_DIR.iterdir()):
            if d.is_dir() and not any(f for f in d.glob("*.json") if not f.name.startswith("_")):
                idx = d / CATEGORY_INDEX_NAME
                if idx.exists():
                    idx.unlink()
                if not any(d.iterdir()):
                    d.rmdir()

    # Generate category indexes
    print("\n" + "-" * 50)
    print("Generating indexes...")

    if LISTS_DIR.exists():
        for category_dir in sorted(LISTS_DIR.iterdir()):
            if not category_dir.is_dir():
                continue
            count = generate_category_index(category_dir)
            print(f"  Generated: lists/{category_dir.name}/{CATEGORY_INDEX_NAME} ({count} items)")

    # Generate root index
    warnings = generate_root_index()
    print(f"  Generated: indexes.json")

    # Print warnings
    if warnings:
        print("\n" + "-" * 50)
        for w in warnings:
            print(f"  {w}")

    # Summary
    print("\n" + "=" * 50)
    print(f"Summary: {valid_count} valid, {invalid_count} invalid")
    print("=" * 50)

    if invalid_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
