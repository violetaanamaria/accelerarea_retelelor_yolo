#!/usr/bin/env python3

import argparse
import json
import random
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from scenarios.categories import SCENARIOS

COCO_JSON_URL = "http://images.cocodataset.org/annotations/instances_val2017.json"
COCO_ANN_ZIP_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
COCO_ANN_ZIP_MEMBER = "annotations/instances_val2017.json"
COCO_IMAGE_URL = "http://images.cocodataset.org/val2017/{filename}"

# COCO category_id -> name (subset relevant)
COCO_ID_TO_NAME = {
    1: "person",
    2: "bicycle",
    3: "car",
    4: "motorcycle",
    6: "bus",
    8: "truck",
    10: "traffic light",
    13: "stop sign",
    17: "cat",
    18: "dog",
}

SCENARIO_CATEGORY_IDS: Dict[str, List[int]] = {
    "persoane": [1],
    "vehicule": [2, 3, 4, 6, 8],
    "animale": [17, 18],
    "semne": [10, 13],
}


def download_file(url: str, dest: Path, force: bool = False) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        print(f"  OK: Există deja: {dest.name}")
        return True
    print(f"  Descarcare Descărcare {dest.name}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  OK: Salvat: {dest}")
        return True
    except urllib.error.URLError as e:
        print(f"  EROARE: Eroare descărcare {url}: {e}")
        return False


def ensure_annotations_json(json_path: Path, force: bool = False) -> bool:
    """Obține instances_val2017.json (direct sau din zip-ul oficial COCO)."""
    if json_path.exists() and not force:
        print(f"  OK: Annotări: {json_path}")
        return True

    json_path.parent.mkdir(parents=True, exist_ok=True)

    print("  Descarcare Încerc descărcare directă instances_val2017.json...")
    if download_file(COCO_JSON_URL, json_path, force=force):
        return True

    zip_path = json_path.parent / "annotations_trainval2017.zip"
    print("  Descarcare Fallback: annotations_trainval2017.zip (~241 MB, o singură dată)...")
    if not download_file(COCO_ANN_ZIP_URL, zip_path, force=force):
        return False

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            if COCO_ANN_ZIP_MEMBER not in zf.namelist():
                print(f"  EROARE: Lipsă {COCO_ANN_ZIP_MEMBER} în arhivă")
                return False
            print(f"  Extrag {COCO_ANN_ZIP_MEMBER}...")
            with zf.open(COCO_ANN_ZIP_MEMBER) as src, open(json_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        print(f"  OK: Annotări extrase: {json_path}")
        return True
    except zipfile.BadZipFile as e:
        print(f"  EROARE: Arhivă invalidă: {e}")
        return False


def load_coco_annotations(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_image_index(coco: dict):
    """image_id -> {file_name, category_ids, category_names}"""
    id_to_name = {cat["id"]: cat["name"] for cat in coco["categories"]}

    image_map = {img["id"]: img["file_name"] for img in coco["images"]}
    image_categories: Dict[int, Set[int]] = defaultdict(set)

    for ann in coco["annotations"]:
        image_categories[ann["image_id"]].add(ann["category_id"])

    index = {}
    for image_id, cat_ids in image_categories.items():
        if image_id not in image_map:
            continue
        names = {id_to_name[cid] for cid in cat_ids if cid in id_to_name}
        index[image_id] = {
            "file_name": image_map[image_id],
            "category_ids": cat_ids,
            "category_names": names,
        }
    return index


STRATIFIED_GROUPS: Dict[str, List[tuple]] = {
    "animale": [(17, "cat"), (18, "dog")],
    "semne": [(13, "stop sign"), (10, "traffic light")],
}


def _make_candidate(image_id: int, meta: dict, wanted_ids: Set[int]) -> dict:
    matched = meta["category_ids"] & wanted_ids
    matched_names = [
        COCO_ID_TO_NAME[cid] for cid in matched if cid in COCO_ID_TO_NAME
    ]
    return {
        "image_id": image_id,
        "file_name": meta["file_name"],
        "matched_categories": sorted(set(matched_names)),
    }


def select_images_for_scenario(
    image_index: dict,
    scenario_key: str,
    per_scenario: int,
    seed: int,
) -> List[dict]:
    wanted_ids = set(SCENARIO_CATEGORY_IDS[scenario_key])
    candidates = []

    for image_id, meta in image_index.items():
        matched = meta["category_ids"] & wanted_ids
        if not matched:
            continue
        candidates.append(_make_candidate(image_id, meta, wanted_ids))

    rng = random.Random(seed)
    rng.shuffle(candidates)
    return candidates[:per_scenario]


def select_images_stratified(
    image_index: dict,
    scenario_key: str,
    per_scenario: int,
    seed: int,
) -> List[dict]:
    """Selecție echilibrată pe subcategorii (cat/dog, stop sign/traffic light)."""
    groups = STRATIFIED_GROUPS[scenario_key]
    wanted_ids = set(SCENARIO_CATEGORY_IDS[scenario_key])
    rng = random.Random(seed)

    buckets: Dict[str, List[dict]] = {}
    for cat_id, name in groups:
        bucket = []
        for image_id, meta in image_index.items():
            if cat_id in meta["category_ids"]:
                bucket.append(_make_candidate(image_id, meta, wanted_ids))
        rng.shuffle(bucket)
        buckets[name] = bucket

    n = len(groups)
    base = per_scenario // n
    extra = per_scenario % n
    quotas = [base + (1 if i < extra else 0) for i in range(n)]

    # Ajustează dacă o subcategorie are prea puține imagini în COCO
    names = [name for _, name in groups]
    available = [len(buckets[name]) for name in names]
    for i, name in enumerate(names):
        if quotas[i] > available[i]:
            shortfall = quotas[i] - available[i]
            quotas[i] = available[i]
            # redistribuie surplusul către bucket-ul cu cele mai multe imagini rămase
            while shortfall > 0:
                best = max(
                    range(n),
                    key=lambda j: available[j] - quotas[j],
                )
                if available[best] <= quotas[best]:
                    break
                quotas[best] += 1
                shortfall -= 1

    selected: List[dict] = []
    selected_ids: Set[int] = set()

    for (_, name), quota in zip(groups, quotas):
        taken = 0
        for item in buckets[name]:
            if item["image_id"] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item["image_id"])
            taken += 1
            if taken >= quota:
                break

    if len(selected) < per_scenario:
        all_candidates = select_images_for_scenario(
            image_index, scenario_key, len(image_index), seed
        )
        for item in all_candidates:
            if item["image_id"] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item["image_id"])
            if len(selected) >= per_scenario:
                break

    return selected[:per_scenario]


def selection_stats(selected: List[dict]) -> Dict[str, int]:
    from collections import Counter

    counter: Counter = Counter()
    for item in selected:
        for cat in item["matched_categories"]:
            counter[cat] += 1
    return dict(counter)


def ensure_coco_image(
    file_name: str,
    cache_dir: Path,
    force: bool = False,
) -> Path:
    dest = cache_dir / file_name
    if dest.exists() and not force:
        return dest
    url = COCO_IMAGE_URL.format(filename=file_name)
    if not download_file(url, dest, force=force):
        raise FileNotFoundError(f"Nu s-a putut descărca {file_name}")
    return dest


def copy_to_scenario(
    src: Path,
    scenario_key: str,
    dest_name: str,
    scenarios_root: Path,
    dry_run: bool,
) -> Path:
    folder = scenarios_root / SCENARIOS[scenario_key]["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / dest_name
    if dry_run:
        print(f"    [dry-run] → {dest}")
        return dest
    shutil.copy2(src, dest)
    return dest


def clear_scenario_folders(scenarios_root: Path, scenario_keys: List[str]):
    for key in scenario_keys:
        folder = scenarios_root / SCENARIOS[key]["folder"]
        if not folder.exists():
            continue
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            for f in folder.glob(ext):
                f.unlink()
        print(f"  Golit: {folder}")


def write_manifest(manifest_path: Path, manifest: dict, dry_run: bool):
    if dry_run:
        return
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Descarcă subset COCO val2017 pentru cele 4 scenarii experimentale"
    )
    parser.add_argument(
        "--per-scenario", type=int, default=15,
        help="Număr imagini per scenariu (default: 15)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Seed pentru selecție reproducibilă (default: 42)",
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help="Cale locală la instances_val2017.json (sare descărcarea JSON)",
    )
    parser.add_argument(
        "--coco-dir",
        type=Path,
        default=None,
        help="Folder cu imagini val2017 deja extrase (ex: coco/val2017)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=ROOT / "datasets" / "coco" / "cache" / "val2017",
        help="Cache descărcări imagini individuale",
    )
    parser.add_argument(
        "--scenarios-root",
        type=Path,
        default=ROOT / "datasets" / "test_scenarios",
        help="Destinație scenarii",
    )
    parser.add_argument(
        "--scenario", choices=list(SCENARIOS.keys()),
        help="Procesează un singur scenariu",
    )
    parser.add_argument(
        "--clear", action="store_true",
        help="Șterge imaginile existente din folderele scenariilor înainte de copiere",
    )
    parser.add_argument(
        "--force-download", action="store_true",
        help="Re-descarcă JSON și imagini chiar dacă există",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Afișează planul fără descărcare/copiere",
    )
    args = parser.parse_args()

    scenario_keys = [args.scenario] if args.scenario else list(SCENARIOS.keys())

    print("=" * 60)
    print("  DESCĂRCARE COCO → 4 SCENARII")
    print("=" * 60)
    print(f"  Imagini/scenariu: {args.per_scenario}")
    print(f"  Scenarii:         {', '.join(scenario_keys)}")
    print()

    # Annotations JSON
    json_path = args.annotations
    if json_path is None:
        json_path = ROOT / "datasets" / "coco" / "instances_val2017.json"

    if args.dry_run:
        if not json_path.exists():
            print(f"  [dry-run] Ar descărca annotări → {json_path}")
    elif not ensure_annotations_json(json_path, force=args.force_download):
        print("\n[EROARE] Nu am putut obține annotările COCO.")
        print("   Descarcă manual arhiva și extrage JSON-ul:")
        print(f"   curl -L {COCO_ANN_ZIP_URL} -o {json_path.parent / 'annotations_trainval2017.zip'}")
        print(f"   unzip -p annotations_trainval2017.zip {COCO_ANN_ZIP_MEMBER} > {json_path}")
        return 1

    if args.dry_run:
        print("  [dry-run] Skip parsare JSON completă")
        return 0

    coco = load_coco_annotations(json_path)
    image_index = build_image_index(coco)
    print(f"  OK: Index COCO: {len(image_index)} imagini cu annotări")

    if args.clear:
        clear_scenario_folders(args.scenarios_root, scenario_keys)

    image_source_dir = args.coco_dir
    if image_source_dir:
        image_source_dir = image_source_dir.expanduser().resolve()
        if not image_source_dir.exists():
            print(f"[EROARE] Folder COCO inexistent: {image_source_dir}")
            return 1
        print(f"  OK: Imagini locale: {image_source_dir}")

    args.cache_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"per_scenario": args.per_scenario, "seed": args.seed, "scenarios": {}}
    total_copied = 0

    for scenario_key in scenario_keys:
        meta = SCENARIOS[scenario_key]
        print(f"\n>>> {meta['section']} {meta['title']}")

        wanted_ids = set(SCENARIO_CATEGORY_IDS[scenario_key])
        pool_size = sum(
            1 for meta in image_index.values() if meta["category_ids"] & wanted_ids
        )
        print(f"  Pool COCO disponibil: {pool_size} imagini")

        if scenario_key in STRATIFIED_GROUPS:
            selected = select_images_stratified(
                image_index, scenario_key, args.per_scenario, args.seed
            )
            stats = selection_stats(selected)
            print(f"  Selecție echilibrată: {stats}")
        else:
            selected = select_images_for_scenario(
                image_index, scenario_key, args.per_scenario, args.seed
            )

        print(f"  Selectate: {len(selected)}/{args.per_scenario} imagini")
        if len(selected) < args.per_scenario:
            print(
                f"  [ATENTIE] COCO val2017 are doar {pool_size} imagini pentru acest scenariu — "
                f"imposibil {args.per_scenario}."
            )

        if not selected:
            print("  [ATENTIE] Niciun candidat — verifică annotările COCO")
            continue

        scenario_manifest = []
        copied = 0

        for i, item in enumerate(selected, start=1):
            file_name = item["file_name"]
            stem = Path(file_name).stem
            cats = "_".join(item["matched_categories"][:2]).replace(" ", "-")
            dest_name = f"coco_{stem}_{cats}.jpg"

            try:
                if image_source_dir:
                    src = image_source_dir / file_name
                    if not src.exists():
                        print(f"    EROARE: Lipsă local: {file_name}")
                        continue
                else:
                    src = ensure_coco_image(
                        file_name, args.cache_dir, force=args.force_download
                    )

                dest = copy_to_scenario(
                    src, scenario_key, dest_name,
                    args.scenarios_root, args.dry_run,
                )
                copied += 1
                scenario_manifest.append({
                    "source": file_name,
                    "dest": str(dest.relative_to(ROOT)) if not args.dry_run else dest_name,
                    "categories": item["matched_categories"],
                    "coco_image_id": item["image_id"],
                })
                print(f"    OK: [{i}/{len(selected)}] {dest_name} ← {item['matched_categories']}")

            except FileNotFoundError as e:
                print(f"    EROARE: {e}")

        manifest["scenarios"][scenario_key] = {
            "title": meta["title"],
            "requested": args.per_scenario,
            "copied": copied,
            "images": scenario_manifest,
        }
        total_copied += copied
        print(f"  → Copiate: {copied}/{args.per_scenario}")

    manifest_path = args.scenarios_root / "coco_manifest.json"
    write_manifest(manifest_path, manifest, args.dry_run)

    print("\n" + "=" * 60)
    print(f"[OK] Total imagini copiate: {total_copied}")
    print(f"Scenarii: {args.scenarios_root}")
    if not args.dry_run:
        print(f"Manifest: {manifest_path}")
    print("\nRulează testele:")
    print("   python3 run_scenarios.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
