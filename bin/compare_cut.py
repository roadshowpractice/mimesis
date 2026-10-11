#!/usr/bin/env python3
"""Compare a FULL video with a shorter re-post of it, by transcript, and make a card.

Question it answers: which stretches of the full video does the re-post keep, and which does it cut?
Built for Tim Ballard's Oct 5, 2026 FB reel 1668493984858221 (his re-post of the White House border
remarks) against our full YouTube copy i5ID7VTlLuw. Usable for any full-vs-excerpt pair.

Inputs are the word-timed transcripts dl_wm already writes (<stem>.whisper.json). No pixels are compared
and nothing is fetched. The only pixels used are one frame of the full video for the card picture.

  compare  CASE --full FULL.whisper.json --cut CUT.whisper.json
           Line up the two word lists (difflib), find the kept spans of the full timeline, write
           CASE/out/compare_cut.json + compare_cut.md, and log both inputs' sha256 to CASE/CUSTODY.log.
  card     CASE --keep-quote TEXT --cut-quote TEXT [--title ...] [--frame-at SEC]
           Draw the card from CASE/out/compare_cut.json. Each quote must appear word for word in the
           full transcript, the KEPT one inside a kept span and the CUT one inside a cut span. Otherwise
           it stops. Quotes still need a second Whisper model (or an ear) before posting.

The card never names anyone in our own text: pass labels like "him" / "the re-post".
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

GAP_S = 3.0      # matched runs closer than this (on both timelines) belong to one kept span
DRIFT_S = 1.5    # ...and only if the full-minus-cut time offset moves less than this
MIN_SPAN_WORDS = 4  # shorter matched runs are treated as noise, not as a kept span


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def custody(case, step, msg, path=None):
    line = "{}\t{}\t{}".format(utc_now(), step, msg)
    if path is not None:
        line += "\t{}\tsha256={}".format(path, sha256_file(path))
    with open(Path(case) / "CUSTODY.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def mmss(t):
    t = int(round(t))
    return "{}:{:02d}".format(t // 60, t % 60)


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def load_words(path):
    """[(normalised word, start, end, raw word)] from a whisper.json with word timestamps."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for seg in d["segments"]:
        for w in seg.get("words") or []:
            n = norm(w["word"])
            if n:
                out.append((n, float(w["start"]), float(w["end"]), w["word"].strip()))
    if not out:
        sys.exit("no word timestamps in {}".format(path))
    return out


def media_duration(whisper_json):
    """Duration of the <stem>.mp4 next to the transcript (ffprobe), or None."""
    p = Path(whisper_json)
    mp4 = p.with_name(p.name.replace(".whisper.json", ".mp4"))
    if not mp4.exists():
        return None, None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip()), mp4
    except ValueError:
        return None, mp4


def align(full, cut):
    sm = difflib.SequenceMatcher(None, [w[0] for w in full], [w[0] for w in cut], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    spans = []
    for b in blocks:
        f0, f1 = full[b.a][1], full[b.a + b.size - 1][2]
        c0, c1 = cut[b.b][1], cut[b.b + b.size - 1][2]
        off = f0 - c0
        s = spans[-1] if spans else None
        if s and f0 - s["full_end"] < GAP_S and c0 - s["cut_end"] < GAP_S and abs(off - s["offset"]) < DRIFT_S:
            s.update(full_end=f1, cut_end=c1, words=s["words"] + b.size, full_last=b.a + b.size - 1)
        else:
            spans.append(dict(full_start=f0, full_end=f1, cut_start=c0, cut_end=c1, offset=off,
                              words=b.size, full_first=b.a, full_last=b.a + b.size - 1))
    spans = [s for s in spans if s["words"] >= MIN_SPAN_WORDS]
    # per-word timestamp agreement inside the kept spans
    deltas = []
    for b in blocks:
        for k in range(b.size):
            deltas.append((full[b.a + k][1] - cut[b.b + k][1]))
    matched = sum(b.size for b in blocks)
    return spans, matched, deltas


def cmd_compare(a):
    case = Path(a.case)
    (case / "out").mkdir(parents=True, exist_ok=True)
    full, cut = load_words(a.full), load_words(a.cut)
    full_dur, full_mp4 = media_duration(a.full)
    cut_dur, cut_mp4 = media_duration(a.cut)
    full_dur = full_dur or full[-1][2]
    cut_dur = cut_dur or cut[-1][2]
    spans, matched, deltas = align(full, cut)

    kept, t = [], 0.0
    cuts = []
    for s in spans:
        # snap to the full video's edges when the span starts/ends within a breath of them
        s0 = 0.0 if s["full_start"] < 1.5 else s["full_start"]
        s1 = full_dur if full_dur - s["full_end"] < 1.5 else s["full_end"]
        if s0 - t > 0.5:
            cuts.append([t, s0])
        kept.append([s0, s1])
        t = s1
    if full_dur - t > 0.5:
        cuts.append([t, full_dur])

    def text(i0, i1):
        return " ".join(w[3] for w in full[i0:i1 + 1])

    cut_words = [" ".join(w[3] for w in full if w[1] >= c0 - 0.01 and w[2] <= c1 + 0.01) for c0, c1 in cuts]
    deltas_in = sorted(abs(d - spans[0]["offset"]) for d in deltas) if spans else []
    res = dict(
        made_at=utc_now(), tool="mimesis bin/compare_cut.py",
        full=dict(transcript=str(a.full), sha256=sha256_file(a.full), media=str(full_mp4) if full_mp4 else None,
                  duration=round(full_dur, 2), words=len(full)),
        cut=dict(transcript=str(a.cut), sha256=sha256_file(a.cut), media=str(cut_mp4) if cut_mp4 else None,
                 duration=round(cut_dur, 2), words=len(cut)),
        rules=dict(gap_s=GAP_S, drift_s=DRIFT_S, min_span_words=MIN_SPAN_WORDS),
        cut_words_matched=matched,
        median_abs_time_delta=round(deltas_in[len(deltas_in) // 2], 2) if deltas_in else None,
        kept=[dict(start=round(s0, 2), end=round(s1, 2), words=sp["words"], offset=round(sp["offset"], 2),
                   first_words=text(sp["full_first"], min(sp["full_first"] + 11, sp["full_last"])),
                   last_words=text(max(sp["full_last"] - 11, sp["full_first"]), sp["full_last"]))
              for (s0, s1), sp in zip(kept, spans)],
        cut_spans=[dict(start=round(c0, 2), end=round(c1, 2), text=tx) for (c0, c1), tx in zip(cuts, cut_words)],
    )
    jp = case / "out" / "compare_cut.json"
    jp.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pct = 100.0 * matched / len(cut)
    md = ["# compare_cut: what the re-post keeps and cuts", "",
          "Made {} by mimesis `bin/compare_cut.py` (transcript line-up only, no pixels, no fetching).".format(res["made_at"]),
          "", "| | Full | Re-post |", "|---|---|---|",
          "| Transcript | `{}` | `{}` |".format(a.full, a.cut),
          "| Length | {} | {} |".format(mmss(full_dur), mmss(cut_dur)),
          "| Words (Whisper) | {} | {} |".format(len(full), len(cut)), "",
          "**{} of the re-post's {} words ({:.0f}%) match the full video, in order.**".format(matched, len(cut), pct),
          "Median timestamp disagreement inside the kept span: {} s.".format(res["median_abs_time_delta"]), "",
          "## Kept", ""]
    for k in res["kept"]:
        md.append("- **{}–{}** ({} words): “{} …” → “… {}”".format(mmss(k["start"]), mmss(k["end"]), k["words"],
                                                                 k["first_words"], k["last_words"]))
    md += ["", "## Cut", ""]
    for c in res["cut_spans"]:
        md.append("- **{}–{}** ({:.0f} s): “{}”".format(mmss(c["start"]), mmss(c["end"]), c["end"] - c["start"], c["text"]))
    md += ["", "Words are Whisper's. Re-hear anything before quoting it publicly.", ""]
    mp = case / "out" / "compare_cut.md"
    mp.write_text("\n".join(md), encoding="utf-8")
    custody(case, "compare_cut", "input full transcript", a.full)
    custody(case, "compare_cut", "input re-post transcript", a.cut)
    custody(case, "compare_cut", "wrote", jp)
    custody(case, "compare_cut", "wrote", mp)
    print("\n".join(md))
    print(jp)


def find_quote(words, quote):
    q = [norm(w) for w in quote.split() if norm(w)]
    seq = [w[0] for w in words]
    for i in range(len(seq) - len(q) + 1):
        if seq[i:i + len(q)] == q:
            return words[i][1], words[i + len(q) - 1][2]
    return None


def inside(t0, t1, spans):
    return any(s["start"] - 0.3 <= t0 and t1 <= s["end"] + 0.3 for s in spans)


def wrap(dr, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def cmd_card(a):
    from PIL import Image, ImageDraw, ImageFont

    case = Path(a.case)
    res = json.loads((case / "out" / "compare_cut.json").read_text(encoding="utf-8"))
    full = load_words(res["full"]["transcript"])
    for label, q, spans in (("KEPT", a.keep_quote, res["kept"]), ("CUT", a.cut_quote, res["cut_spans"])):
        hit = find_quote(full, q.replace("|", " ").strip("“”\""))
        if not hit:
            sys.exit("{} quote not found word for word in the full transcript: {!r}".format(label, q))
        if not inside(hit[0], hit[1], spans):
            sys.exit("{} quote is at {}–{}, outside every {} span".format(label, mmss(hit[0]), mmss(hit[1]), label))
        print("{} quote found at {}–{} ✓".format(label, mmss(hit[0]), mmss(hit[1])))

    F = "/usr/share/fonts/truetype/dejavu/"
    bold = lambda s: ImageFont.truetype(F + "DejaVuSans-Bold.ttf", s)
    reg = lambda s: ImageFont.truetype(F + "DejaVuSans.ttf", s)
    serif = lambda s: ImageFont.truetype(F + "DejaVuSerif-Bold.ttf", s)
    BG, FG, DIM, KEEP, CUT, LINE, EDIT = "#101318", "#eef0f4", "#9ca5b4", "#3fb37f", "#e5483a", "#2b313c", "#f2c230"
    W, M = 1080, 56
    im = Image.new("RGB", (W, 2400), BG)
    dr = ImageDraw.Draw(im)

    dr.text((M, 48), a.title, font=bold(96), fill=FG)
    y = 162
    for line in a.subtitle:
        dr.text((M, y), line, font=reg(32), fill=DIM)
        y += 42
    y += 16
    if a.edit_credit:
        head, _, rest = a.edit_credit.partition("|")
        dr.rounded_rectangle((M, y, W - M, y + 68), radius=10, outline=EDIT, width=3)
        dr.text((M + 22, y + 15), head.strip(), font=bold(31), fill=EDIT)
        dr.text((M + 22 + dr.textlength(head.strip() + " ", font=bold(31)), y + 18), rest.strip(), font=reg(28), fill=FG)
        y += 100

    fw = W - 2 * M
    if res["full"]["media"]:
        frame = case / "out" / "compare_cut_frame.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.frame_at), "-i", res["full"]["media"],
                        "-frames:v", "1", str(frame)], check=True)
        fr = Image.open(frame).convert("RGB")
        top, bottom = (int(v) for v in a.frame_crop.split(","))
        fr = fr.crop((0, top, fr.width, fr.height - bottom))
        fr = fr.resize((fw, round(fr.height * fw / fr.width)), Image.LANCZOS)
        im.paste(fr, (M, y))
        dr.rectangle((M - 2, y - 2, M + fw + 1, y + fr.height + 1), outline=LINE, width=2)
        y += fr.height + 40

    # timeline: the full video, green where the re-post keeps it, red where it cuts
    total = res["full"]["duration"]
    x = lambda t: M + fw * t / total
    for spans, col, lab, ink in ((res["kept"], KEEP, "KEPT", "#0b1a12"), (res["cut_spans"], CUT, "CUT", "#2a0905")):
        for s in spans:
            dr.rectangle((x(s["start"]), y, x(s["end"]), y + 54), fill=col)
            t = "{}  {}–{}".format(lab, mmss(s["start"]), mmss(s["end"]))
            if dr.textlength(t, font=bold(28)) + 32 > x(s["end"]) - x(s["start"]):
                t = lab
            if dr.textlength(t, font=bold(28)) + 32 <= x(s["end"]) - x(s["start"]):
                dr.text((x(s["start"]) + 16, y + 10), t, font=bold(28), fill=ink)
    y += 70
    dr.text((M, y), "{} {}".format(a.full_name, mmss(total)), font=reg(24), fill=DIM)
    s = "re-post {}".format(mmss(res["cut"]["duration"]))
    dr.text((W - M - dr.textlength(s, font=reg(24)), y), s, font=reg(24), fill=DIM)
    y += 64

    for label, col, q in (("KEPT", KEEP, a.keep_quote), ("CUT", CUT, a.cut_quote)):
        lines = [l for part in "“{}”".format(q.strip("“”\"")).split("|") for l in wrap(dr, part.strip(), serif(44), fw - 40)]
        dr.rectangle((M, y, M + 10, y + 44 + 56 * len(lines) - 6), fill=col)
        dr.text((M + 34, y), label, font=bold(28), fill=col)
        yy = y + 44
        for line in lines:
            dr.text((M + 34, yy), line, font=serif(44), fill=FG)
            yy += 56
        y = yy + 36

    dr.line((M, y, W - M, y), fill=LINE, width=2)
    y += 24
    y_foot = y
    pct = 100.0 * res["cut_words_matched"] / res["cut"]["words"]
    foot = list(a.footer) + ["Transcripts lined up: {:.0f}% of the re-post's words match the {}, in order.".format(
        pct, a.full_name.lower())]
    for t in foot:
        for line in wrap(dr, t, reg(24), fw - 230):  # keep clear of the sticker's column
            dr.text((M, y), line, font=reg(24), fill=DIM)
            y += 36
    im = im.crop((0, 0, W, max(y + 60, y_foot + 230)))  # room at bottom right for the BUTTFIRE sticker
    out = Path(a.out) if a.out else case / "out" / "compare_cut_card.png"
    im.save(out)
    custody(case, "compare_cut card", "wrote", out)
    print(out, im.size)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("case")
    c.add_argument("--full", required=True, help="full video's .whisper.json")
    c.add_argument("--cut", required=True, help="re-post's .whisper.json")
    k = sub.add_parser("card")
    k.add_argument("case")
    k.add_argument("--keep-quote", required=True, help='"|" forces a line break on the card')
    k.add_argument("--cut-quote", required=True)
    k.add_argument("--title", default="THE CUT")
    k.add_argument("--subtitle", action="append", default=[])
    k.add_argument("--edit-credit", default="", help='"BOLD PART | rest", drawn in a yellow box under the title')
    k.add_argument("--full-name", default="Full speech")
    k.add_argument("--footer", action="append", default=[])
    k.add_argument("--frame-at", type=float, default=20.0, help="seconds into the full video for the picture")
    k.add_argument("--frame-crop", default="0,0", help="pixels to crop off top,bottom (e.g. our own old watermark)")
    k.add_argument("--out")
    a = p.parse_args(argv)
    {"compare": cmd_compare, "card": cmd_card}[a.cmd](a)


if __name__ == "__main__":
    main()
