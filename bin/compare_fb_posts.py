#!/usr/bin/env python3
"""Apples-to-apples comparison of two Facebook photo posts that look alike from the outside.

Question it answers: apart from the words written on them, can the two posts' images be told apart?
Every measurable trait is listed, and each trait gets a verdict:

  SAME              both posts give the same value (within the tolerance fixed in RULES)
  OVERLAP           the posts' value ranges overlap, so the trait can't tell them apart
  DISTINGUISHABLE   the ranges don't overlap, so this trait alone separates the posts

Nothing is OCR'd. If every trait is SAME/OVERLAP, the only thing left to separate them is the text.

Input: two post folders, each holding the images from one post and (optionally) the dl_wm metadata
JSON. A mimesis case folder works too (its raw/ is used). Inputs are only read, never written.

  compare_fb_posts.py A_DIR B_DIR --out OUT_DIR [--label-a TB] [--label-b AM]

Writes OUT_DIR/report.md, features.csv, verdicts.csv, manifest.json, and appends to OUT_DIR/CUSTODY.log.
Images are only compared within the same type (text card vs text card, other vs other).
"""
import argparse
import csv
import glob
import hashlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_x_ig import custody, dhash, hamming, script_identity, sha256_file, utc_now  # noqa: E402

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

# Fixed before any run. Numeric traits: ranges that come within `tol` of each other count as overlapping.
RULES = {
    "aspect": {"tol": 0.002},
    "bytes_per_pixel": {"tol": 0.01},
    "luma_mean": {"tol": 4.0},
    "bg_luma": {"tol": 4.0},
    "ink_luma": {"tol": 8.0},
    "chroma_mean": {"tol": 1.0},
    "ink_coverage": {"tol": 0.01},
    "margin_left": {"tol": 0.02},
    "margin_right": {"tol": 0.02},
    "margin_top": {"tol": 0.03},
    "margin_bottom": {"tol": 0.03},
    "text_lines": {"tol": 0},
    "line_height": {"tol": 0.004},
    "line_pitch": {"tol": 0.006},
    "line_center_offset": {"tol": 0.01},
    "stroke_ratio": {"tol": 0.01},
    "width": {"tol": 0},
    "height": {"tol": 0},
    "file_size": {"tol": 0},
    "text_card_rule": "grayscale (mean |R-G|,|G-B| < 2) and a flat border (border luma std < 6)",
    "ink_rule": "pixels whose luma differs from the border median by > 60",
    "dhash_bits": 64,
}
NUMERIC = [k for k, v in RULES.items() if isinstance(v, dict)]
CATEGORICAL = ["format", "mode", "type", "polarity", "alignment", "exif_tags", "icc_profile", "progressive",
               "subsampling", "quant_tables"]
# Traits that come from Facebook's own re-encode rather than from the poster's file.
PLATFORM_TRAITS = {"format", "mode", "exif_tags", "icc_profile", "progressive", "subsampling", "quant_tables",
                   "bytes_per_pixel", "file_size"}


def find_images(d):
    d = Path(d)
    if (d / "raw").is_dir():
        d = d / "raw"
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
    metas = sorted(p for p in d.glob("*.json"))
    return d, imgs, (metas[0] if metas else None)


def _runs(mask_1d):
    runs, start = [], None
    for i, v in enumerate(list(mask_1d) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    return runs


def image_features(path):
    import numpy as np
    from PIL import Image

    im = Image.open(path)
    f = {"file": path.name, "sha256": sha256_file(path), "file_size": path.stat().st_size,
         "format": im.format, "mode": im.mode, "width": im.width, "height": im.height,
         "aspect": round(im.width / im.height, 4)}
    f["bytes_per_pixel"] = round(f["file_size"] / (im.width * im.height), 4)
    f["exif_tags"] = len(im.getexif())
    f["icc_profile"] = bool(im.info.get("icc_profile"))
    f["progressive"] = bool(im.info.get("progressive") or im.info.get("progression"))
    q = getattr(im, "quantization", None) or {}
    f["quant_tables"] = hashlib.sha256(json.dumps({k: list(v) for k, v in q.items()}).encode()).hexdigest()[:12] if q else "none"
    try:
        from PIL import JpegImagePlugin
        f["subsampling"] = {0: "4:4:4", 1: "4:2:2", 2: "4:2:0"}.get(JpegImagePlugin.get_sampling(im), "n/a")
    except Exception:
        f["subsampling"] = "n/a"

    # Work at a fixed width so layout numbers are comparable across resolutions.
    W = 800
    rgb = np.asarray(im.convert("RGB").resize((W, round(W * im.height / im.width)), Image.LANCZOS), dtype=np.float32)
    luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    H = luma.shape[0]
    f["luma_mean"] = round(float(luma.mean()), 1)
    f["chroma_mean"] = round(float((np.abs(rgb[..., 0] - rgb[..., 1]) + np.abs(rgb[..., 1] - rgb[..., 2])).mean() / 2), 2)
    b = max(4, W // 100)
    border = np.concatenate([luma[:b].ravel(), luma[-b:].ravel(), luma[:, :b].ravel(), luma[:, -b:].ravel()])
    bg = float(np.median(border))
    f["bg_luma"] = round(bg, 1)
    f["type"] = "text_card" if f["chroma_mean"] < 2 and float(border.std()) < 6 else "other"
    f["polarity"] = "light_on_dark" if bg < 128 else "dark_on_light"

    ink = np.abs(luma - bg) > 60
    f["ink_coverage"] = round(float(ink.mean()), 4)
    f["ink_luma"] = round(float(luma[ink].mean()), 1) if ink.any() else None
    rows, cols = np.where(ink)
    if rows.size:
        f["margin_top"], f["margin_bottom"] = round(rows.min() / H, 4), round(1 - (rows.max() + 1) / H, 4)
        f["margin_left"], f["margin_right"] = round(cols.min() / W, 4), round(1 - (cols.max() + 1) / W, 4)
    lines = [r for r in _runs(ink.any(axis=1)) if r[1] - r[0] >= 3]  # text lines = runs of rows holding ink
    f["text_lines"] = len(lines)
    if lines:
        f["line_height"] = round(float(np.median([e - s for s, e in lines])) / H, 4)
        if len(lines) > 1:
            f["line_pitch"] = round(float(np.median([lines[i + 1][0] - lines[i][0] for i in range(len(lines) - 1)])) / H, 4)
        offsets = []
        for s, e in lines:
            c = np.where(ink[s:e].any(axis=0))[0]
            offsets.append(((c.min() + c.max() + 1) / 2 - W / 2) / W)
        f["line_center_offset"] = round(float(np.median(np.abs(offsets))), 4)
        lefts = [np.where(ink[s:e].any(axis=0))[0].min() / W for s, e in lines]
        f["alignment"] = "center" if f["line_center_offset"] < 0.02 and np.std(lefts) > 0.01 else (
            "left" if np.std(lefts) <= 0.01 else "mixed")
        # stroke weight: ink pixels per unit of text-line area
        area = sum((e - s) for s, e in lines) * W
        f["stroke_ratio"] = round(float(ink.sum()) / area, 4) if area else None
    f["dhash"] = "%016x" % dhash(im)
    return f


def load_post(d, label):
    root, imgs, meta_path = find_images(d)
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path else {}
    return {"label": label, "dir": str(root), "meta_file": str(meta_path) if meta_path else None,
            "meta": {k: meta.get(k) for k in ("source_url", "uploader", "creation_time", "caption", "media_type")},
            "images": [image_features(p) for p in imgs]}


def _num_verdict(av, bv, tol):
    if not av or not bv:
        return "n/a"
    a0, a1, b0, b1 = min(av), max(av), min(bv), max(bv)
    if a1 - a0 <= tol and b1 - b0 <= tol and abs(a0 - b0) <= tol:
        return "SAME"
    if a0 <= b1 + tol and b0 <= a1 + tol:
        return "OVERLAP"
    return "DISTINGUISHABLE"


def _cat_verdict(av, bv):
    if not av or not bv:
        return "n/a"
    sa, sb = set(map(str, av)), set(map(str, bv))
    if sa == sb and len(sa) == 1:
        return "SAME"
    if sa & sb:
        return "OVERLAP"
    return "DISTINGUISHABLE"


def _fmt(vals):
    if not vals:
        return "-"
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        lo, hi = min(vals), max(vals)
        return str(lo) if lo == hi else "{} .. {}".format(lo, hi)
    return ", ".join(sorted(set(map(str, vals))))


def compare(A, B):
    verdicts = []
    types = sorted({i["type"] for i in A["images"]} | {i["type"] for i in B["images"]})
    for t in types:
        a = [i for i in A["images"] if i["type"] == t]
        b = [i for i in B["images"] if i["type"] == t]
        for k in CATEGORICAL + NUMERIC:
            av = [i[k] for i in a if i.get(k) is not None]
            bv = [i[k] for i in b if i.get(k) is not None]
            v = _num_verdict(av, bv, RULES[k]["tol"]) if k in NUMERIC else _cat_verdict(av, bv)
            verdicts.append({"type": t, "trait": k, "source": "platform" if k in PLATFORM_TRAITS else "poster",
                             "A": _fmt(av), "B": _fmt(bv), "verdict": v})
    # post-level traits
    for k, fn in [("image_count", lambda P: [len(P["images"])]),
                  ("type_mix", lambda P: [",".join(sorted("{}x{}".format(sum(1 for i in P["images"] if i["type"] == t), t)
                                                         for t in {i["type"] for i in P["images"]}))])]:
        av, bv = fn(A), fn(B)
        verdicts.append({"type": "post", "trait": k, "source": "poster", "A": _fmt(av), "B": _fmt(bv),
                         "verdict": "SAME" if av == bv else "DISTINGUISHABLE"})
    # nearest cross-post image fingerprint, same type only
    cross = []
    for ia in A["images"]:
        best = min(((hamming(int(ia["dhash"], 16), int(ib["dhash"], 16)), ib["file"]) for ib in B["images"]
                    if ib["type"] == ia["type"] and ib["sha256"] != ia["sha256"]), default=None)
        same_bytes = [ib["file"] for ib in B["images"] if ib["sha256"] == ia["sha256"]]
        cross.append({"A": ia["file"], "type": ia["type"], "identical_bytes_in_B": ";".join(same_bytes),
                      "nearest_B": best[1] if best else "", "dhash_distance": best[0] if best else ""})
    return verdicts, cross


def write_outputs(out, A, B, verdicts, cross):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "features.csv", "w", newline="", encoding="utf-8") as fh:
        keys = ["post", "file"] + [k for k in A["images"][0].keys() if k != "file"] if A["images"] else ["post", "file"]
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for P in (A, B):
            for i in P["images"]:
                w.writerow({"post": P["label"], **i})
    with open(out / "verdicts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["type", "trait", "source", "A", "B", "verdict"])
        w.writeheader()
        w.writerows(verdicts)

    dist = [v for v in verdicts if v["verdict"] == "DISTINGUISHABLE"]
    poster_dist = [v for v in dist if v["source"] == "poster"]
    L = ["# Apples-to-apples: {} vs {}".format(A["label"], B["label"]), "",
         "Run {} UTC. No OCR. Verdicts: SAME / OVERLAP = can't tell the posts apart on that trait; "
         "DISTINGUISHABLE = the trait alone separates them.".format(utc_now()), ""]
    for P in (A, B):
        m = P["meta"]
        L += ["- **{}**: {} image(s) from `{}`; uploader {}, posted {}, url {}".format(
            P["label"], len(P["images"]), P["dir"], m.get("uploader"), m.get("creation_time"), m.get("source_url"))]
    L += ["", "## Bottom line", ""]
    if not poster_dist:
        L += ["No poster-side trait separates the two posts. Apart from the text on them, they look the same "
              "(only OCR / text recovery would tell them apart)."]
    else:
        L += ["{} poster-side trait(s) separate the posts: {}.".format(
            len(poster_dist), ", ".join("{} ({})".format(v["trait"], v["type"]) for v in poster_dist))]
    if dist and len(dist) != len(poster_dist):
        L += ["", "Platform-side differences (from Facebook's re-encode, not the poster): {}.".format(
            ", ".join(v["trait"] for v in dist if v["source"] == "platform"))]
    for title, want in [("Distinguishable", {"DISTINGUISHABLE"}), ("Not distinguishable", {"SAME", "OVERLAP"}),
                        ("Not measurable", {"n/a"})]:
        rows = [v for v in verdicts if v["verdict"] in want]
        L += ["", "## {} ({})".format(title, len(rows)), "", "| type | trait | source | {} | {} | verdict |".format(
            A["label"], B["label"]), "|---|---|---|---|---|---|"]
        L += ["| {type} | {trait} | {source} | {A} | {B} | {verdict} |".format(**v) for v in rows]
    L += ["", "## Nearest {} image for each {} image (dHash, 64 bits; same type only)".format(B["label"], A["label"]), "",
          "| {} | type | identical bytes in {} | nearest | distance |".format(A["label"], B["label"]), "|---|---|---|---|---|"]
    L += ["| {A} | {type} | {identical_bytes_in_B} | {nearest_B} | {dhash_distance} |".format(**c) for c in cross]
    L += ["", "## Rules (fixed before the run)", "", "```", json.dumps(RULES, indent=1), "```", ""]
    (out / "report.md").write_text("\n".join(L), encoding="utf-8")
    manifest = {"run_utc": utc_now(), "tool": script_identity(), "rules": RULES,
                "inputs": {P["label"]: {"dir": P["dir"], "meta_file": P["meta_file"],
                                        "images": {i["file"]: i["sha256"] for i in P["images"]}} for P in (A, B)}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("a_dir")
    ap.add_argument("b_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A, B = load_post(args.a_dir, args.label_a), load_post(args.b_dir, args.label_b)
    for P in (A, B):
        if not P["images"]:
            sys.exit("no images in {}".format(P["dir"]))
        for i in P["images"]:
            custody(out, "read", "{} {}".format(P["label"], i["file"]), Path(P["dir"]) / i["file"])
    verdicts, cross = compare(A, B)
    write_outputs(out, A, B, verdicts, cross)
    custody(out, "compare", "{} vs {}: {} traits, {} distinguishable".format(
        A["label"], B["label"], len(verdicts), sum(v["verdict"] == "DISTINGUISHABLE" for v in verdicts)),
        out / "report.md")
    print(out / "report.md")


if __name__ == "__main__":
    main()
