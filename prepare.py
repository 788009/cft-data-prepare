import json
from pathlib import Path
import shutil
import pandas as pd
import os
import fnmatch

MUNICIPALITIES = {"北京", "北京市", "天津", "天津市", "上海", "上海市", "重庆", "重庆市"}

EXCLUDE_PATTERNS = {
    'data.csv'
}

def is_excluded(path: Path, base_dir: Path, patterns: set) -> bool:
    """根据规则集合判断指定路径是否应当排除"""
    rel_path = path.relative_to(base_dir).as_posix()
    path_parts = rel_path.split("/")

    for pattern in patterns:
        clean_pattern = pattern.rstrip("/")
        if fnmatch.fnmatch(rel_path, clean_pattern) or any(
            fnmatch.fnmatch(part, clean_pattern) for part in path_parts
        ):
            return True
    return False

def copy_remaining_files(
    src_dir: str, dest_dir: str, exclude_patterns: set = EXCLUDE_PATTERNS
) -> None:
    """执行文件复制业务逻辑，仅处理未被排除的文件与目录"""
    src_path = Path(src_dir).resolve()
    dest_path = Path(dest_dir).resolve()

    for root, dirs, files in os.walk(src_path):
        current_dir = Path(root)

        dirs[:] = [
            d
            for d in dirs
            if not is_excluded(current_dir / d, src_path, exclude_patterns)
        ]

        for file_name in files:
            file_path = current_dir / file_name
            if is_excluded(file_path, src_path, exclude_patterns):
                continue

            rel_path = file_path.relative_to(src_path)
            target_file_path = dest_path / rel_path
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_file_path)


def process_data():
    base_dir = Path(".")
    prepare_dir = base_dir / "prepare"
    temp_dir = base_dir / "temp"
    data_dir = base_dir / "data"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    geojson_prov_out = temp_dir / "geojson" / "provinces"
    geojson_city_out = temp_dir / "geojson" / "cities"

    try:
        geojson_prov_out.mkdir(parents=True, exist_ok=True)
        geojson_city_out.mkdir(parents=True, exist_ok=True)

        # 1. 读取 data.csv
        data_csv_path = prepare_dir / "data.csv"
        df_data = pd.read_csv(data_csv_path, dtype=str)

        # 2. 读取 university_location.json 追加经纬度并更新大学名称
        uni_path = base_dir / "university_location.json"
        uni_location = {}
        if uni_path.exists():
            with uni_path.open("r", encoding="utf-8") as f:
                uni_location = json.load(f)

        lat_list = []
        lng_list = []
        updated_universities = []

        for _, row in df_data.iterrows():
            lat, lng = "", ""
            univ = str(row.get("university", "")).strip()

            if univ in uni_location:
                coords = uni_location[univ]
                lat, lng = coords[0], coords[1]
            else:
                univ_en = univ.replace("（", "(").replace("）", ")")
                if univ_en != univ and univ_en in uni_location:
                    coords = uni_location[univ_en]
                    lat, lng = coords[0], coords[1]
                    univ = univ_en

            updated_universities.append(univ)
            lat_list.append(lat)
            lng_list.append(lng)

        if "university" in df_data.columns:
            df_data["university"] = updated_universities
        df_data["lat"] = lat_list
        df_data["lng"] = lng_list

        # 3. 读取 ok_data_level3.csv 构建全国名称到 adcode 的映射表
        level3_path = base_dir / "ok_data_level3.csv"
        df_level3 = pd.read_csv(level3_path, dtype=str)

        all_prov_map = {}
        all_city_map = {}

        for _, row in df_level3.iterrows():
            deep = str(row["deep"]).strip()
            name = str(row["name"]).strip()
            ext_id = str(row["ext_id"]).strip()
            adcode = ext_id[:6]

            if deep == "0":
                all_prov_map[name] = adcode
            elif deep == "1":
                all_city_map[name] = adcode

        # 4. 过滤仅保留 data.csv 中用到的省份与城市
        used_provinces = (
            set(df_data["province"].dropna().str.strip())
            if "province" in df_data.columns
            else set()
        )
        used_cities = (
            set(df_data["city"].dropna().str.strip())
            if "city" in df_data.columns
            else set()
        )

        province2adcode = {
            p: all_prov_map[p] for p in used_provinces if p in all_prov_map
        }
        cities2adcode = {
            c: all_city_map[c]
            for c in used_cities
            if c in all_city_map
            and c not in MUNICIPALITIES
            and not all_city_map[c].startswith(("11", "12", "31", "50"))
        }

        with (temp_dir / "province2adcode.json").open("w", encoding="utf-8") as f:
            json.dump(province2adcode, f, ensure_ascii=False, indent=2)

        with (temp_dir / "cities2adcode.json").open("w", encoding="utf-8") as f:
            json.dump(cities2adcode, f, ensure_ascii=False, indent=2)

        # 5. 保存更新后的 data.csv
        df_data.to_csv(temp_dir / "data.csv", index=False, encoding="utf-8")

        # 6. 复制用到的省份 GeoJSON
        src_prov_dir = base_dir / "geojson" / "provinces"
        if src_prov_dir.exists():
            for adcode in province2adcode.values():
                src_file = src_prov_dir / f"{adcode}.json"
                if src_file.exists():
                    shutil.copy(
                        src_file, geojson_prov_out / f"{adcode}.json"
                    )

        # 7. 复制用到的城市 GeoJSON 并平铺输出
        src_city_dir = base_dir / "geojson" / "cities"
        if src_city_dir.exists():
            city_file_map = {p.stem: p for p in src_city_dir.rglob("*.json")}

            for adcode in cities2adcode.values():
                if adcode in city_file_map:
                    shutil.copy(
                        city_file_map[adcode], geojson_city_out / f"{adcode}.json"
                    )

        # 8. 递归复制其余未排除的文件至 temp 目录
        copy_remaining_files(prepare_dir, temp_dir, EXCLUDE_PATTERNS)

        # 组装成功后，移除已有 data 目录并替换
        if data_dir.exists():
            shutil.rmtree(data_dir)
        temp_dir.rename(data_dir)

    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


if __name__ == "__main__":
    process_data()
