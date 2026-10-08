#!/usr/bin/env python3
"""Compare one X account's posts with one Instagram account's posts, forensically.

Question it answers: do the two accounts share content (same text, same media, same links),
or only topics, or nothing? Built for X @ldsabuse vs Instagram ldsabuseonx (Oct 2026), usable
for any pair.

A CASE folder holds everything (keep it under data/, which git ignores):

  00_PREDICTION.md         predictions + decision rules, written BEFORE collection
  CUSTODY.log              append-only: every step, UTC time, what was read or written, sha256
  x/raw/<id>.json          each X post exactly as X's public embed endpoint served it (bytes untouched)
  x/media/<id>_<n>.<ext>   photos / video posters attached to those posts
  ig/capture/              a copy of a bin/ig_scrape_account.py capture from dl_wm (posts.jsonl, manifest.json, raw)
  ig/media/<code>/         a copy of the post's media and its .srt transcript (from dl_wm outputs)
  derived/frames/          video frames sampled for image fingerprints (re-creatable)
  out/                     report.md, pairs.csv, manifest.json

Steps (each one writes to CUSTODY.log):
  fetch-x  CASE --ids FILE [FILE...]   download each X post's raw JSON + attached images (network)
  fetch-x-media CASE                   download each X video's best MP4 variant, from the saved raw JSON
  files    CASE                        file-level inventory of every media file on both sides (ffprobe/EXIF),
                                       then cross-checks: identical bytes, same durations, shared encoder tags
  add-ig   CASE --capture DIR [--media DIR...]   copy (never move) the Instagram data in
  compare  CASE [--window-days 1]      offline. Re-checks every input hash first, stops on any mismatch
  ledger   CASE [--out FILE]           offline. One row per Instagram post, keyed by its code (never by day):
                                       own/collab, file on disk, best X match within +/-3 days, and a status.
                                       Test lists come from this file, not retyped from a write-up (T4 lost a
                                       post that way: Aug 12 had 2 posts, one matched, and the day got ticked off)

Rules (THRESHOLDS below) are fixed before the comparison and written into out/manifest.json.
Pair classes, strongest first:
  IDENTICAL       same image (dHash distance <= 6), same link, or text 5-word-shingle Jaccard >= 0.8
  SAME MATERIAL   near image (<= 12), shared run of >= 8 words, >= 2 shared 5-word shingles,
                  or the same uncommon link domain
  TOPIC ONLY      >= 3 shared uncommon content words
  NOTHING SHARED  none of the above
Control: same-day pairs (|day difference| <= window) are compared with pairs from other days. If topic
overlap is no higher on the same day, timing isn't telling us anything.

Python 3.8+ (mimesis venv). Uses Pillow + numpy for image hashes, ffmpeg for video frames.
"""
import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

THRESHOLDS = {
    "img_identical": 6,          # dHash Hamming distance (64-bit)
    "img_near": 12,
    "shingle_n": 5,              # words per shingle
    "shingle_jaccard_identical": 0.8,
    "shared_shingles_material": 2,
    "common_run_material": 8,    # longest run of identical words
    "rare_terms_topic": 3,       # shared uncommon content words
    "rare_df_max": 0.10,         # "uncommon" = in at most 10% of all items (both sides), but never fewer than 2
    "frame_every_s": 2.0,        # video frame sampling for fingerprints
    "tz_offset_hours": -7,       # day boundaries in PDT
}
GENERIC_DOMAINS = {"x.com", "twitter.com", "t.co", "instagram.com", "www.instagram.com", "youtu.be",
                   "youtube.com", "www.youtube.com", "facebook.com", "tiktok.com", "linktr.ee"}
STOP = set("""a an and are as at be been but by can could did do does for from had has have he her him his how i if in
into is it its just like me more my no not now of on or our out she so some than that the their them then there these
they this to too up us was we were what when where which who why will with would you your yeah yes all about any
because been being dont don't im i'm it's its thats that's ive i've youre you're get got going gonna one also only
very really even still ever every here over such much many most other own same should than through while
""".split())
SYND = "https://cdn.syndication.twimg.com/tweet-result?id={id}&lang=en&token={tok}"


# ---------- custody + hashing ----------

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def custody(case, step, msg, path=None):
    line = "{}\t{}\t{}".format(utc_now(), step, msg)
    if path is not None:
        line += "\t{}\tsha256={}".format(os.path.relpath(str(path), str(case)), sha256_file(path))
    with open(Path(case) / "CUSTODY.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def script_identity():
    me = Path(__file__).resolve()
    try:
        commit = subprocess.run(["git", "-C", str(me.parent), "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(me.parent), "status", "--porcelain", str(me)],
                                    capture_output=True, text=True).stdout.strip())
    except Exception:
        commit, dirty = "", None
    return {"script": str(me), "sha256": sha256_file(me), "git_commit": commit, "script_uncommitted": dirty,
            "python": sys.version.split()[0], "host": socket.gethostname()}


# ---------- text features ----------

URL_RE = re.compile(r"https?://\S+")


def norm_url(u):
    u = u.strip().rstrip(".,)!?;:'\"")
    u = re.sub(r"^https?://(www\.)?", "", u.lower())
    u = u.split("#")[0]
    u = re.sub(r"[?&](utm_[^&]*|igsh=[^&]*|s=\d+|t=[^&]*)", "", u)
    return u.rstrip("/?")


def domain(u):
    return norm_url(u).split("/")[0]


def tokens(text):
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = URL_RE.sub(" ", t)
    t = t.replace("’", "'")
    return re.findall(r"[a-z0-9][a-z0-9']*", t)


def content_words(toks):
    return {w for w in toks if len(w) >= 4 and w not in STOP and not w.isdigit()}


def shingles(toks, n):
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def longest_run(a, b):
    if not a or not b:
        return 0
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return m.size


def srt_text(path):
    out = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.isdigit() or "-->" in s:
            continue
        out.append(s)
    return " ".join(out)


# ---------- image fingerprints ----------

def dhash(path_or_img):
    from PIL import Image
    import numpy as np
    img = path_or_img if hasattr(path_or_img, "convert") else Image.open(path_or_img)
    g = np.asarray(img.convert("L").resize((9, 8), Image.LANCZOS), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a, b):
    return bin(a ^ b).count("1")


def video_frames(video, outdir, every):
    outdir.mkdir(parents=True, exist_ok=True)
    if not any(outdir.glob("f_*.jpg")):
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=1/{}".format(every),
                        "-q:v", "4", str(outdir / "f_%05d.jpg")], check=False)
    return sorted(outdir.glob("f_*.jpg"))


# ---------- step 1: fetch X ----------

def x_token(tid):
    # token used by X's embed widget: ((id / 1e15) * pi) in base 36 without zeros or the dot
    import math
    v = (int(tid) / 1e15) * math.pi
    ip, fp = int(v), v - int(v)
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    s = ""
    while ip:
        s = digits[ip % 36] + s
        ip //= 36
    s = (s or "0") + "."
    for _ in range(10):
        fp *= 36
        s += digits[int(fp)]
        fp -= int(fp)
    return re.sub(r"(0+|\.)", "", s)


def read_ids(files):
    ids = []
    for f in files:
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            m = re.search(r"\b(\d{15,20})\b", line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
    return ids


def cmd_fetch_x(a):
    import requests
    case = Path(a.case)
    ids = read_ids(a.ids)
    custody(case, "fetch-x", "start: {} ids from {}".format(len(ids), ", ".join(a.ids)))
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0"
    for n, tid in enumerate(ids, 1):
        raw = case / "x" / "raw" / "{}.json".format(tid)
        if raw.exists():
            continue
        for attempt in range(5):
            r = sess.get(SYND.format(id=tid, tok=x_token(tid) if attempt % 2 == 0 else "4"), timeout=30)
            if r.status_code == 404 and attempt == 0:
                continue   # some IDs only answer with the short token
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                print("  429 rate limit, waiting {}s".format(wait))
                time.sleep(wait)
                continue
            break
        if r.status_code != 200 or not r.content.strip().startswith(b"{"):
            custody(case, "fetch-x", "FAILED {} http {} ({} bytes)".format(tid, r.status_code, len(r.content)))
            print("[{}/{}] {} FAILED http {}".format(n, len(ids), tid, r.status_code))
            time.sleep(a.pause)
            continue
        raw.write_bytes(r.content)
        custody(case, "fetch-x", "saved post {}".format(tid), raw)
        d = json.loads(r.content)
        for k, med in enumerate(d.get("mediaDetails") or []):
            url = med.get("media_url_https")
            if not url:
                continue
            ext = url.rsplit(".", 1)[-1].split("?")[0] or "jpg"
            mp = case / "x" / "media" / "{}_{}.{}".format(tid, k, ext)
            mr = sess.get(url + "?name=large", timeout=60)
            if mr.status_code == 200:
                mp.write_bytes(mr.content)
                custody(case, "fetch-x", "saved media {} ({})".format(tid, med.get("type")), mp)
        print("[{}/{}] {} ok".format(n, len(ids), tid))
        time.sleep(a.pause)
    custody(case, "fetch-x", "done")


# ---------- step 1b: X videos (from the saved raw JSON) ----------

def cmd_fetch_x_media(a):
    import requests
    case = Path(a.case)
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0"
    custody(case, "fetch-x-media", "start")
    for raw in sorted((case / "x" / "raw").glob("*.json")):
        d = json.loads(raw.read_bytes())
        for k, med in enumerate(d.get("mediaDetails") or []):
            vi = med.get("video_info") or {}
            mp4s = [v for v in vi.get("variants") or [] if v.get("content_type") == "video/mp4" and v.get("url")]
            if not mp4s:
                continue
            best = max(mp4s, key=lambda v: v.get("bitrate") or 0)
            dst = case / "x" / "media" / "{}_{}.mp4".format(raw.stem, k)
            if dst.exists():
                continue
            r = sess.get(best["url"], timeout=120)
            if r.status_code == 200 and r.content:
                dst.write_bytes(r.content)
                custody(case, "fetch-x-media", "saved video {} ({} kbps variant)".format(
                    raw.stem, (best.get("bitrate") or 0) // 1000), dst)
            else:
                custody(case, "fetch-x-media", "FAILED video {} http {}".format(raw.stem, r.status_code))
            time.sleep(a.pause)
    custody(case, "fetch-x-media", "done")


# ---------- file-level inventory ----------

MEDIA_EXT = {".mp4", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".webp", ".gif"}


def probe(path):
    """Container/stream facts and tags as ffprobe reports them (no decoding of content)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except ValueError:
        return {}


def image_meta(path):
    out = {}
    try:
        from PIL import Image
        im = Image.open(path)
        out["pil_format"] = im.format
        ex = im.getexif() if hasattr(im, "getexif") else {}
        for tag, name in ((305, "exif_software"), (306, "exif_datetime"), (271, "exif_make"), (272, "exif_model")):
            if ex and ex.get(tag):
                out[name] = str(ex.get(tag))
        icc = im.info.get("icc_profile")
        out["icc_profile"] = hashlib.sha256(icc).hexdigest()[:12] if icc else ""
        out["jfif"] = "jfif" in im.info
    except Exception as e:
        out["pil_error"] = str(e)[:60]
    return out


def file_row(case, side, owner_id, path):
    pr = probe(path)
    fmt = pr.get("format") or {}
    v = next((s for s in pr.get("streams") or [] if s.get("codec_type") == "video"), {})
    au = next((s for s in pr.get("streams") or [] if s.get("codec_type") == "audio"), {})
    tags = dict(fmt.get("tags") or {})
    vt = v.get("tags") or {}
    row = {
        "side": side, "item": owner_id, "file": os.path.relpath(str(path), str(case)),
        "sha256": sha256_file(path), "bytes": path.stat().st_size,
        "container": fmt.get("format_name", ""), "duration_s": round(float(fmt.get("duration") or 0), 2),
        "bitrate_kbps": int(float(fmt.get("bit_rate") or 0) / 1000),
        "vcodec": v.get("codec_name", ""), "profile": v.get("profile", ""), "pix_fmt": v.get("pix_fmt", ""),
        "width": v.get("width", ""), "height": v.get("height", ""), "fps": v.get("r_frame_rate", ""),
        "acodec": au.get("codec_name", ""), "sample_rate": au.get("sample_rate", ""),
        "encoder": tags.get("encoder", "") or vt.get("encoder", ""),
        "major_brand": tags.get("major_brand", ""), "compatible_brands": tags.get("compatible_brands", ""),
        "creation_time": tags.get("creation_time", "") or vt.get("creation_time", ""),
        "handler": vt.get("handler_name", ""), "vendor": vt.get("vendor_id", ""),
        "other_tags": ";".join("{}={}".format(k, tags[k]) for k in sorted(tags)
                               if k not in ("encoder", "major_brand", "minor_version", "compatible_brands",
                                            "creation_time"))[:200],
    }
    if path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        row.update(image_meta(path))
    return row


def cmd_files(a):
    case = Path(a.case)
    checked, problems = verify_custody(case)
    if problems:
        sys.exit("input check FAILED:\n  " + "\n  ".join(problems))
    rows = []
    for f in sorted((case / "x" / "media").iterdir()):
        if f.suffix.lower() in MEDIA_EXT:
            rows.append(file_row(case, "X", f.name.split("_")[0], f))
    for d in sorted((case / "ig" / "media").iterdir()) if (case / "ig" / "media").exists() else []:
        for f in sorted(d.iterdir()):
            if f.suffix.lower() in MEDIA_EXT:
                rows.append(file_row(case, "IG", d.name, f))
    out = case / "out"
    out.mkdir(exist_ok=True)
    cols = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("side", "item", "file", "sha256"), k))
    with open(out / "files.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    xs = [r for r in rows if r["side"] == "X"]
    igs = [r for r in rows if r["side"] == "IG"]
    L = ["# File-level comparison: X vs Instagram", "",
         "Run {} UTC. {} X files, {} Instagram files. Inputs re-hashed first: {} files, all match.".format(
             utc_now(), len(xs), len(igs), checked), ""]

    def counts(sel, key):
        c = {}
        for r in sel:
            k = r.get(key) or "-"
            c[k] = c.get(k, 0) + 1
        return ", ".join("{} x{}".format(k, n) for k, n in sorted(c.items(), key=lambda kv: -kv[1]))
    L += ["## What each side's files look like", "", "| Property | X | Instagram |", "|---|---|---|"]
    for key in ("container", "vcodec", "profile", "pix_fmt", "acodec", "sample_rate", "encoder", "major_brand",
                "compatible_brands", "handler", "vendor", "pil_format", "exif_software", "icc_profile"):
        L.append("| {} | {} | {} |".format(key, counts(xs, key), counts(igs, key)))
    L += ["", "## Cross-checks", ""]
    same_hash = [(x, i) for x in xs for i in igs if x["sha256"] == i["sha256"]]
    L.append("- Byte-identical files on both sides: **{}**".format(len(same_hash)))
    for x, i in same_hash:
        L.append("  - {} == {}".format(x["file"], i["file"]))
    xv = [r for r in xs if r["vcodec"] and r["duration_s"] > 0.5]
    iv = [r for r in igs if r["vcodec"] and r["duration_s"] > 0.5]
    dur = [(x, i) for x in xv for i in iv if abs(x["duration_s"] - i["duration_s"]) <= a.dur_tol]
    L.append("- Videos with the same duration (within {}s): **{}**".format(a.dur_tol, len(dur)))
    for x, i in dur:
        L.append("  - {} ({}s, {}x{}) ~ {} ({}s, {}x{})".format(x["file"], x["duration_s"], x["width"], x["height"],
                                                             i["file"], i["duration_s"], i["width"], i["height"]))
    enc = sorted({r["encoder"] for r in xs if r["encoder"]} & {r["encoder"] for r in igs if r["encoder"]})
    L.append("- Encoder tags found on both sides: **{}**".format(", ".join(enc) if enc else "none"))
    exs = sorted({r.get("exif_software") for r in xs if r.get("exif_software")} &
                 {r.get("exif_software") for r in igs if r.get("exif_software")})
    L.append("- Image EXIF 'Software' found on both sides: **{}**".format(", ".join(exs) if exs else "none"))
    L += ["", "Note: both platforms re-encode uploads, so matching platform tags (e.g. an Instagram or X "
          "encoder string) say nothing about who made a file. Identical hashes or matching durations of "
          "user-made video are what would tie the two sides together.", ""]
    (out / "files_report.md").write_text("\n".join(L), encoding="utf-8")
    for n in ("files.csv", "files_report.md"):
        custody(case, "files", "wrote " + n, out / n)
    print("\n".join(L))


# ---------- step 2: add Instagram ----------

def cmd_add_ig(a):
    case = Path(a.case)
    cap = Path(a.capture)
    for name in ("posts.jsonl", "manifest.json", "profile.json", "raw_responses.jsonl.gz", "run.log"):
        src = cap / name
        if src.exists():
            dst = case / "ig" / "capture" / name
            shutil.copy2(src, dst)
            if sha256_file(src) != sha256_file(dst):
                sys.exit("copy check failed: {}".format(src))
            custody(case, "add-ig", "copied {} from {}".format(name, src), dst)
    man = cap / "manifest.json"
    if man.exists():
        listed = json.loads(man.read_text()).get("files") or json.loads(man.read_text()).get("outputs") or {}
        for name, info in (listed.items() if isinstance(listed, dict) else []):
            want = info.get("sha256") if isinstance(info, dict) else None
            got = case / "ig" / "capture" / name
            if want and got.exists() and sha256_file(got) != want:
                custody(case, "add-ig", "WARNING capture manifest hash differs for {}".format(name))
    for mdir in a.media or []:
        mdir = Path(mdir)
        code = re.sub(r"^instagram__", "", mdir.name)
        dst_dir = case / "ig" / "media" / code
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(mdir.iterdir()):
            if f.is_file() and f.suffix.lower() in (".mp4", ".jpg", ".jpeg", ".png", ".webp", ".srt", ".json", ".txt"):
                if "_wm" in f.stem or "watermark" in f.stem:
                    continue   # compare the originals, not our watermarked copies
                dst = dst_dir / f.name
                shutil.copy2(f, dst)
                custody(case, "add-ig", "copied {} for {} from {}".format(f.name, code, mdir), dst)


# ---------- step 3: compare ----------

def verify_custody(case):
    """Every file the log says was saved must still have that hash. Returns (checked, problems)."""
    problems, checked, latest = [], 0, {}
    for line in (Path(case) / "CUSTODY.log").read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 5 and parts[4].startswith("sha256="):
            latest[parts[3]] = parts[4][7:]
    for rel, want in latest.items():
        p = Path(case) / rel
        checked += 1
        if not p.exists():
            problems.append("missing: " + rel)
        elif sha256_file(p) != want:
            problems.append("changed since logged: " + rel)
    return checked, problems


def local_day(ts_utc):
    return (ts_utc + timedelta(hours=THRESHOLDS["tz_offset_hours"])).date()


def x_items(case):
    items = []
    for raw in sorted((case / "x" / "raw").glob("*.json")):
        d = json.loads(raw.read_bytes())
        text = d.get("text") or ""
        note = ((d.get("note_tweet") or {}).get("note_tweet_results") or {}).get("result") or {}
        if len(note.get("text") or "") > len(text):
            text = note["text"]
        ents = d.get("entities") or {}
        urls = [u.get("expanded_url") for u in ents.get("urls") or [] if u.get("expanded_url")]
        ts = datetime.strptime(d["created_at"].replace(".000Z", "Z"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        imgs = sorted((case / "x" / "media").glob("{}_*".format(raw.stem)))
        items.append({
            "side": "X", "id": raw.stem, "ts": ts, "kind": "reply" if d.get("in_reply_to_screen_name") else "post",
            "text": text, "urls": urls,
            "mentions": sorted({m.get("screen_name", "").lower() for m in ents.get("user_mentions") or []}),
            "hashtags": sorted({h.get("text", "").lower() for h in ents.get("hashtags") or []}),
            "images": imgs, "link": "https://x.com/i/status/{}".format(raw.stem)})
    return items


def ig_items(case, account):
    items = []
    posts = case / "ig" / "capture" / "posts.jsonl"
    for line in posts.read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        code = p["code"]
        mdir = case / "ig" / "media" / code
        srts = sorted(mdir.glob("*.srt")) if mdir.exists() else []
        transcript = " ".join(srt_text(s) for s in srts)
        caption = p.get("caption") or ""
        imgs, vids = [], []
        if mdir.exists():
            imgs = [f for f in sorted(mdir.iterdir()) if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            vids = [f for f in sorted(mdir.iterdir()) if f.suffix.lower() == ".mp4"]
        items.append({
            "side": "IG", "id": code, "ts": datetime.fromtimestamp(p["taken_at"], timezone.utc),
            "kind": "own" if p.get("owner") == account else "collab ({})".format(p.get("owner")),
            "text": (caption + " " + transcript).strip(), "has_transcript": bool(srts),
            "urls": URL_RE.findall(caption),
            "mentions": sorted(set(m.lower() for m in re.findall(r"@([\w.]+)", caption))),
            "hashtags": sorted(set(h.lower() for h in re.findall(r"#(\w+)", caption))),
            "images": imgs, "videos": vids, "link": "https://www.instagram.com/p/{}/".format(code)})
    return items


def fingerprints(case, item):
    fps = []
    for img in item.get("images") or []:
        try:
            fps.append((dhash(img), img.name))
        except Exception:
            pass
    for v in item.get("videos") or []:
        for fr in video_frames(v, case / "derived" / "frames" / v.stem, THRESHOLDS["frame_every_s"]):
            try:
                fps.append((dhash(fr), "{}@{}".format(v.name, fr.stem)))
            except Exception:
                pass
    return fps


def score_pair(x, ig, df, n_items):
    T = THRESHOLDS
    xt, it = x["toks"], ig["toks"]
    sx, si = shingles(xt, T["shingle_n"]), shingles(it, T["shingle_n"])
    shared_sh = sx & si
    jac = len(shared_sh) / len(sx | si) if (sx | si) else 0.0
    run = longest_run(xt, it)
    xu, iu = {norm_url(u) for u in x["urls"]}, {norm_url(u) for u in ig["urls"]}
    same_urls = sorted(xu & iu)
    xd = {domain(u) for u in x["urls"]} - GENERIC_DOMAINS
    idm = {domain(u) for u in ig["urls"]} - GENERIC_DOMAINS
    same_domains = sorted(xd & idm)
    cap = max(2, T["rare_df_max"] * n_items)
    rare = sorted(w for w in (x["words"] & ig["words"]) if df.get(w, 0) <= cap)
    best_img, best_img_where = None, ""
    for hx, wx in x["fps"]:
        for hi, wi in ig["fps"]:
            d = hamming(hx, hi)
            if best_img is None or d < best_img:
                best_img, best_img_where = d, "{} ~ {}".format(wx, wi)
    reasons = []
    if best_img is not None and best_img <= T["img_identical"]:
        reasons.append("same image (d={}: {})".format(best_img, best_img_where))
    if same_urls:
        reasons.append("same link: " + ", ".join(same_urls))
    if jac >= T["shingle_jaccard_identical"]:
        reasons.append("text near-identical (Jaccard {:.2f})".format(jac))
    if reasons:
        cls = "IDENTICAL"
    else:
        if best_img is not None and best_img <= T["img_near"]:
            reasons.append("near image (d={}: {})".format(best_img, best_img_where))
        if run >= T["common_run_material"]:
            reasons.append("shared run of {} words".format(run))
        if len(shared_sh) >= T["shared_shingles_material"]:
            reasons.append("{} shared {}-word phrases".format(len(shared_sh), T["shingle_n"]))
        if same_domains:
            reasons.append("same link domain: " + ", ".join(same_domains))
        if reasons:
            cls = "SAME MATERIAL"
        elif len(rare) >= T["rare_terms_topic"]:
            cls = "TOPIC ONLY"
            reasons.append("shared uncommon words: " + ", ".join(rare[:12]))
        else:
            cls = "NOTHING SHARED"
    return {"class": cls, "jaccard": round(jac, 3), "longest_run": run, "shared_phrases": len(shared_sh),
            "same_urls": same_urls, "same_domains": same_domains, "rare_shared": rare,
            "best_image_distance": best_img, "reasons": "; ".join(reasons),
            "example_phrases": sorted(shared_sh)[:3]}


ORDER = ["IDENTICAL", "SAME MATERIAL", "TOPIC ONLY", "NOTHING SHARED"]


def cmd_compare(a):
    case = Path(a.case)
    checked, problems = verify_custody(case)
    if problems:
        custody(case, "compare", "STOPPED: {} input problems".format(len(problems)))
        sys.exit("input check FAILED, nothing compared:\n  " + "\n  ".join(problems))
    custody(case, "compare", "start: {} logged files re-hashed, all match".format(checked))
    xs, igs = x_items(case), ig_items(case, a.account)
    if a.own_only:
        igs = [i for i in igs if i["kind"] == "own"]
    for it in xs + igs:
        it["toks"] = tokens(it["text"])
        it["words"] = content_words(it["toks"])
        it["fps"] = fingerprints(case, it)
        it["day"] = local_day(it["ts"])
    df = {}
    for it in xs + igs:
        for w in it["words"]:
            df[w] = df.get(w, 0) + 1
    n_items = len(xs) + len(igs)
    rows = []
    for ig in igs:
        for x in xs:
            gap = abs((x["day"] - ig["day"]).days)
            s = score_pair(x, ig, df, n_items)
            s.update({"ig": ig["id"], "ig_kind": ig["kind"], "ig_day": str(ig["day"]), "x": x["id"],
                      "x_kind": x["kind"], "x_day": str(x["day"]), "day_gap": gap,
                      "same_day": gap <= a.window_days})
            rows.append(s)
    out = case / "out"
    out.mkdir(exist_ok=True)
    cols = ["ig", "ig_kind", "ig_day", "x", "x_kind", "x_day", "day_gap", "same_day", "class", "jaccard",
            "longest_run", "shared_phrases", "best_image_distance", "same_urls", "same_domains", "rare_shared",
            "reasons"]
    with open(out / "pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (ORDER.index(r["class"]), r["ig_day"], r["ig"], r["x"])):
            w.writerow([";".join(r[c]) if isinstance(r[c], list) else r[c] for c in cols])

    def tally(sel):
        t = {k: 0 for k in ORDER}
        for r in sel:
            t[r["class"]] += 1
        return t, len(sel)
    same, other = [r for r in rows if r["same_day"]], [r for r in rows if not r["same_day"]]
    ts, ns = tally(same)
    to, no = tally(other)
    strong = [r for r in rows if r["class"] in ("IDENTICAL", "SAME MATERIAL")]
    L = ["# X @{} vs Instagram {}: content comparison".format(a.x_account, a.account), "",
         "Run {} UTC by {} (sha256 {}). Inputs: {} X items, {} Instagram items ({} with transcripts). "
         "Every logged input file re-hashed before the run: {} files, all match.".format(
             utc_now(), Path(__file__).name, script_identity()["sha256"][:16], len(xs), len(igs),
             sum(1 for i in igs if i.get("has_transcript")), checked), "",
         "## Result", "",
         "| Class | Same-day pairs (gap <= {}) | Other-day pairs (control) |".format(a.window_days), "|---|---|---|"]
    for k in ORDER:
        L.append("| {} | {} ({:.1%}) | {} ({:.1%}) |".format(k, ts[k], ts[k] / ns if ns else 0, to[k],
                                                             to[k] / no if no else 0))
    L += ["| total | {} | {} |".format(ns, no), "",
          "**Pairs sharing content (IDENTICAL or SAME MATERIAL): {}.**".format(len(strong)), ""]
    if strong:
        L += ["## Every pair that shares content", ""]
        for r in sorted(strong, key=lambda r: (ORDER.index(r["class"]), r["ig_day"])):
            L.append("- **{}**: IG {} ({}, {}) <-> X {} ({}, {}): {}".format(
                r["class"], r["ig"], r["ig_kind"], r["ig_day"], r["x"], r["x_kind"], r["x_day"], r["reasons"]))
        L.append("")
    L += ["## Rules used (fixed before the run)", "", "```", json.dumps(THRESHOLDS, indent=1), "```", "",
          "Method: text = X post text vs Instagram caption + transcript; words lower-cased, links removed; "
          "'uncommon' words appear in at most {:.0%} of all items. Images: 64-bit dHash of X photos/posters vs "
          "Instagram images and video frames every {}s. Day boundaries in UTC{:+d}.".format(
              THRESHOLDS["rare_df_max"], THRESHOLDS["frame_every_s"], THRESHOLDS["tz_offset_hours"]), "",
          "Limits: X plain reposts and deleted posts aren't in the input; a transcript is only as good as "
          "Whisper; an image edited heavily (crop, overlay) can escape dHash.", ""]
    (out / "report.md").write_text("\n".join(L), encoding="utf-8")
    manifest = {"run_utc": utc_now(), "tool": script_identity(), "thresholds": THRESHOLDS,
                "params": {"window_days": a.window_days, "account": a.account, "x_account": a.x_account,
                           "own_only": a.own_only},
                "inputs_checked": checked,
                "outputs": {n: sha256_file(out / n) for n in ("pairs.csv", "report.md")}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for n in ("pairs.csv", "report.md", "manifest.json"):
        custody(case, "compare", "wrote " + n, out / n)
    print("\n".join(L[:14 + len(ORDER)]))


# ---------- per-post ledger ----------

LEDGER_RULE = {"window_days": 3, "len_tol_s": 0.2, "dhash_max": 5, "fracs": (0.3, 0.5, 0.7)}


def _trim_black(img, sides_only):
    import numpy as np
    a = np.asarray(img.convert("L"))
    cols, rows = np.where(a.max(axis=0) > 1)[0], np.where(a.max(axis=1) > 1)[0]
    if not len(cols) or not len(rows):
        return img
    y0, y1 = (0, a.shape[0]) if sides_only else (rows.min(), rows.max() + 1)
    return img.crop((cols.min(), y0, cols.max() + 1, y1))


def _frame(video, t):
    from io import BytesIO
    from PIL import Image
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", "{:.3f}".format(t), "-i", str(video),
                                   "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
    return Image.open(BytesIO(raw))


def _video_print(video):
    """length, and dHash at 30/50/70% raw and with pure-black side bars trimmed (Instagram pads tall video, T3)"""
    d = float((probe(video).get("format") or {}).get("duration") or 0)
    frames = [_frame(video, d * f) for f in LEDGER_RULE["fracs"]]
    return d, [dhash(f) for f in frames], [dhash(_trim_black(f, True)) for f in frames]


def cmd_ledger(a):
    from PIL import Image
    case = Path(a.case)
    R = LEDGER_RULE
    pdt = timezone(timedelta(hours=THRESHOLDS["tz_offset_hours"]))
    xs = []
    for raw in sorted((case / "x" / "raw").glob("*.json")):
        d = json.loads(raw.read_bytes())
        if ((d.get("user") or {}).get("screen_name") or "").lower() != a.x_account.lower():
            continue
        ts = datetime.strptime(d["created_at"].replace(".000Z", "Z"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        files = sorted((case / "x" / "media").glob("{}_*".format(raw.stem)))
        vids = [f for f in files if f.suffix == ".mp4"]
        photos = [f for f in files if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
                  and f.stem not in {v.stem for v in vids}]
        xs.append({"id": raw.stem, "day": ts.astimezone(pdt).date(), "vids": vids, "photos": photos})
    x_days = {i["day"] for i in xs}
    vcache = {}

    def vp(p):
        if p not in vcache:
            vcache[p] = _video_print(p)
        return vcache[p]

    rows = []
    for line in (case / "ig" / "capture" / "posts.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        code = p["code"]
        day = datetime.fromtimestamp(p["taken_at"], timezone.utc).astimezone(pdt).date()
        mdir = case / "ig" / "media" / code
        mp4 = sorted(mdir.glob("*.mp4")) if mdir.exists() else []
        img = sorted(f for f in mdir.glob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")) if mdir.exists() else []
        win_days = {day + timedelta(k) for k in range(-R["window_days"], R["window_days"] + 1)}
        covered = len(win_days & x_days)
        win = [i for i in xs if i["day"] in win_days]
        row = {"code": code, "day_pdt": day.isoformat(), "own": "own" if p.get("owner") == a.account else "collab",
               "owner": p.get("owner"), "ig_media": "video" if mp4 else ("photo" if img else "none"),
               "x_days_with_data": "{}/{}".format(covered, len(win_days)), "best_x": "", "len_diff_s": "",
               "dhash_raw": "", "dhash_sides_trimmed": "", "status": ""}
        best = None
        if mp4:
            L, H, Ht = vp(mp4[0])
            for i in win:
                for v in i["vids"]:
                    xl, xh, xht = vp(v)
                    raw_d, trim_d = max(hamming(q, r) for q, r in zip(H, xh)), max(hamming(q, r) for q, r in zip(Ht, xht))
                    key = (trim_d, abs(xl - L))
                    if best is None or key < best[0]:
                        best = (key, i["id"], abs(xl - L), raw_d, trim_d)
            if best:
                row.update(best_x=best[1], len_diff_s="{:.2f}".format(best[2]), dhash_raw=best[3], dhash_sides_trimmed=best[4])
                hit = best[2] <= R["len_tol_s"] and best[4] <= R["dhash_max"]
        elif img:
            h = dhash(_trim_black(Image.open(img[0]), False))
            for i in win:
                for ph in i["photos"]:
                    dd = hamming(h, dhash(_trim_black(Image.open(ph), False)))
                    if best is None or dd < best[0]:
                        best = (dd, i["id"])
            if best:
                row.update(best_x=best[1], dhash_raw=best[0])
                hit = best[0] <= R["dhash_max"]
        if row["ig_media"] == "none":
            row["status"] = "NO FILE"
        elif covered == 0:
            row["status"] = "NOT SEARCHED"
        elif best and hit:
            row["status"] = "MATCHED"
        else:
            row["status"] = "UNMATCHED" if covered == len(win_days) else "UNMATCHED (partial X coverage)"
        rows.append(row)
    out = Path(a.out) if a.out else case / "out" / "ig_ledger.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0])
    with open(out, "w", encoding="utf-8") as f:
        f.write("# rule: " + json.dumps(LEDGER_RULE) + " ; video MATCHED = pure-black side bars trimmed from both, then len diff <= len_tol_s and dHash <= dhash_max at every frac (raw dHash shown, not used)\n")
        f.write("\t".join(cols) + "\n")
        for r in sorted(rows, key=lambda r: (r["day_pdt"], r["code"])):
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    custody(case, "ledger", "{} Instagram posts, {} X posts".format(len(rows), len(xs)), out)
    from collections import Counter
    for kind in ("own", "collab"):
        sel = [r for r in rows if r["own"] == kind]
        print("{:6s} {:3d}  {}".format(kind, len(sel), ", ".join("{} {}".format(n, s) for s, n in sorted(Counter(r["status"] for r in sel).items()))))
    print("wrote", out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch-x")
    f.add_argument("case")
    f.add_argument("--ids", nargs="+", required=True, help="files with one X status ID per line (TSV ok)")
    f.add_argument("--pause", type=float, default=3.0)
    fm = sub.add_parser("fetch-x-media")
    fm.add_argument("case")
    fm.add_argument("--pause", type=float, default=3.0)
    fl = sub.add_parser("files")
    fl.add_argument("case")
    fl.add_argument("--dur-tol", type=float, default=0.5)
    g = sub.add_parser("add-ig")
    g.add_argument("case")
    g.add_argument("--capture", required=True, help="a bin/ig_scrape_account.py output folder (dl_wm)")
    g.add_argument("--media", nargs="*", help="dl_wm outputs/<date>/instagram__<code>/ folders")
    c = sub.add_parser("compare")
    c.add_argument("case")
    c.add_argument("--account", default="ldsabuseonx")
    c.add_argument("--x-account", default="ldsabuse")
    c.add_argument("--window-days", type=int, default=1)
    c.add_argument("--own-only", action="store_true", help="only Instagram posts the account started itself")
    lg = sub.add_parser("ledger")
    lg.add_argument("case")
    lg.add_argument("--account", default="ldsabuseonx")
    lg.add_argument("--x-account", default="ldsabuse")
    lg.add_argument("--out", help="default: CASE/out/ig_ledger.tsv")
    a = ap.parse_args(argv)
    Path(a.case).mkdir(parents=True, exist_ok=True)
    {"fetch-x": cmd_fetch_x, "fetch-x-media": cmd_fetch_x_media, "files": cmd_files, "add-ig": cmd_add_ig,
     "compare": cmd_compare, "ledger": cmd_ledger}[a.cmd](a)


if __name__ == "__main__":
    main()
