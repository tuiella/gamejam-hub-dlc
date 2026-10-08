"""Build GameJam Hub DLC packs from the human-editable sources in src/.

    python build.py

src/<pack>/pack.json     {"id", "name", "description", "version"}
src/<pack>/*.md          Markdown document template   (first line "<!-- hint: ... -->" optional)
src/<pack>/*.sheet.csv   planning sheet template      (first row = header; "=..." cells are formulas)
src/<pack>/*.diagram.json  diagram template (GameJam Hub diagram JSON)
src/<pack>/*.moodboard.json moodboard template

Writes packs/<id>.json and index.json (with each pack's size and SHA-256, which the hub
checks before installing). Data only: packs never contain code.
"""
import csv, hashlib, io, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEAD = {"bl": 1, "bg": "#e6efe9", "fc": "#1f4d40"}


def hint_of(text):
    m = re.match(r"\s*<!--\s*hint:\s*(.*?)\s*-->\s*\n", text)
    return (m.group(1), text[m.end():]) if m else ("", text)


def name_of(path, suffix):
    return os.path.basename(path)[: -len(suffix)]


def typed(s):
    t = s.strip()
    try:
        return int(t)
    except ValueError:
        pass
    try:
        return float(t)
    except ValueError:
        return s


def col_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def eval_simple(f, grid):
    """Value of =A1/B1-style formulas so the sheet shows numbers when first opened."""
    def ref(m):
        c = 0
        for ch in m.group(1).upper():
            c = c * 26 + ord(ch) - 64
        r = int(m.group(2)) - 1
        v = grid[r][c - 1] if r < len(grid) and c - 1 < len(grid[r]) else None
        return f"({v})" if isinstance(v, (int, float)) else "None"
    expr = re.sub(r"([A-Za-z]+)(\d+)", ref, f.lstrip("="))
    if not re.fullmatch(r"[\d+\-*/().\sNone]*", expr) or "None" in expr:
        return None
    try:
        v = eval(expr, {"__builtins__": {}})
        return round(v, 6)
    except Exception:
        return None


def sheet_from_csv(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f)]
    grid = [[typed(c) if c and not c.startswith("=") else c for c in r] for r in rows]
    cells = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == "":
                continue
            if r == 0:
                cells.append({"r": r, "c": c, "v": {"v": v, "m": str(v), **HEAD, "ct": {"fa": "General", "t": "g"}}})
            elif isinstance(v, str) and v.startswith("="):
                val = eval_simple(v, grid)
                cell = {"f": v, "ct": {"fa": "General", "t": "n"}}
                if val is not None:
                    cell.update(v=val, m=str(val))
                cells.append({"r": r, "c": c, "v": cell})
            else:
                cells.append({"r": r, "c": c, "v": {"v": v, "m": str(v), "ct": {"fa": "General", "t": "n" if isinstance(v, (int, float)) else "g"}}})
    widths = {}
    for c in range(max((len(r) for r in rows), default=0)):
        longest = max((len(str(r[c])) for r in rows if c < len(r)), default=4)
        widths[str(c)] = max(70, min(260, longest * 13 + 24))
    name = name_of(path, ".sheet.csv")
    return {"v": 1, "sheets": [{"name": name, "celldata": cells, "config": {"columnlen": widths}, "frozen": {"type": "row"}}]}


def build_pack(folder):
    meta = json.load(io.open(os.path.join(folder, "pack.json"), encoding="utf-8"))
    templates = []
    for fn in sorted(os.listdir(folder)):
        path = os.path.join(folder, fn)
        if fn.endswith(".md"):
            hint, body = hint_of(io.open(path, encoding="utf-8").read())
            templates.append({"kind": "md", "id": fn[:-3], "name": fn[:-3], "hint": hint, "content": body})
        elif fn.endswith(".sheet.csv"):
            hint_file = path[:-4] + ".hint"
            hint = io.open(hint_file, encoding="utf-8").read().strip() if os.path.exists(hint_file) else ""
            templates.append({"kind": "sheet", "id": name_of(fn, ".sheet.csv"), "name": name_of(fn, ".sheet.csv"), "hint": hint, "content": json.dumps(sheet_from_csv(path), ensure_ascii=False)})
        elif fn.endswith(".diagram.json") or fn.endswith(".moodboard.json"):
            kind = "diagram" if fn.endswith(".diagram.json") else "moodboard"
            data = json.load(io.open(path, encoding="utf-8"))
            hint = data.pop("hint", "")
            templates.append({"kind": kind, "id": name_of(fn, f".{kind}.json"), "name": name_of(fn, f".{kind}.json"), "hint": hint, "content": json.dumps(data, ensure_ascii=False)})
    pack = {"v": 1, "id": meta["id"], "name": meta["name"], "description": meta.get("description", ""), "version": meta["version"], "templates": templates}
    return pack


def main():
    index = {"v": 1, "packs": []}
    src = os.path.join(ROOT, "src")
    os.makedirs(os.path.join(ROOT, "packs"), exist_ok=True)
    for name in sorted(os.listdir(src)):
        folder = os.path.join(src, name)
        if not os.path.isfile(os.path.join(folder, "pack.json")):
            continue
        pack = build_pack(folder)
        data = json.dumps(pack, ensure_ascii=False, indent=1).encode("utf-8")
        rel = f"packs/{pack['id']}.json"
        io.open(os.path.join(ROOT, rel), "wb").write(data)
        index["packs"].append({
            "id": pack["id"], "name": pack["name"], "description": pack["description"], "version": pack["version"],
            "templates": len(pack["templates"]), "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "path": rel,
        })
        print(f"{pack['id']} v{pack['version']}: {len(pack['templates'])} templates, {len(data)} bytes")
    io.open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(index, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    sys.exit(main())
