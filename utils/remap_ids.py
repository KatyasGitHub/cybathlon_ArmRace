#!/usr/bin/env python
"""
Remap YOLO class-IDs inside every .txt file under a given directory.
Example:
    python utils/remap_ids.py \
           --dir dataset/labels_all \
           --map 15:0 16:1 17:2
"""

import argparse, pathlib, sys

# ──────────────────────────────────────────────────────────────────────────────
def parse_pairs(pairs):
    """Convert ['15:0', '16:1'] → {15: 0, 16: 1} and validate."""
    mapping = {}
    for p in pairs:
        try:
            old, new = map(int, p.split(":"))
        except ValueError:
            sys.exit(f"bad pair '{p}'. Use old:new, e.g. 15:0")
        mapping[old] = new
    return mapping


def remap_file(txt_path: pathlib.Path, mapping: dict[int, int]) -> bool:
    """Rewrite a single label file; return True if it changed."""
    changed = False
    new_lines = []

    for line in txt_path.read_text().strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        cls_id = int(float(parts[0]))      # tolerate '15.0'
        if cls_id in mapping:
            parts[0] = str(mapping[cls_id])
            changed = True
        new_lines.append(" ".join(parts))

    if changed:
        txt_path.write_text("\n".join(new_lines) + "\n")
    return changed


def main():
    ap = argparse.ArgumentParser(description="Remap YOLO class-IDs in label txts")
    ap.add_argument("--dir", "-d", required=True,
                    help="root folder that contains .txt label files")
    ap.add_argument("--map", nargs="+", required=True,
                    help="space-separated list like 15:0 16:1 17:2")
    args = ap.parse_args()

    root = pathlib.Path(args.dir)
    if not root.exists():
        sys.exit(f"directory not found: {root}")

    mapping = parse_pairs(args.map)
    txt_files = list(root.rglob("*.txt"))

    print(f"🔍  scanning {len(txt_files)} files under {root} …")
    n_fixed = sum(remap_file(f, mapping) for f in txt_files)
    print(f"✅  rewrote {n_fixed} file(s); others already OK.")


if __name__ == "__main__":
    main()
