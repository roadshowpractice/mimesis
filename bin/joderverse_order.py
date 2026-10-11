#!/usr/bin/env python3
"""Order the posts of a collaborator network in time, compute its symmetry group, and say where marked posts sit.

The network as an incidence structure (the notation of "Automorphism Group of the Incidence Structure and Its Orbits"):
  points = accounts; one block per post = the account that posted it + every account credited on it.
Reads a posts TSV with columns: code, taken_at_utc, started_by, collaborators (';'-separated).

  joderverse_order.py POSTS.tsv --mark DcR9bobtKcF=B7 --mark Dbed4OEN_9d=B1 ... [--sage PATH] [--out DIR]

Prints and writes (to --out):
  order.tsv   every post in time order: rank, time (UTC), code, label (if marked), the block's accounts
  report.md   |Aut| (the group's order) and its orbits, and for each marked post: its time rank among all posts
              and among the marked posts
Group: plain-Python backtracking (like verify_automorphisms.py: replication r and pair counts lambda prune, each complete
relabelling checked against the multiset of blocks), cross-checked in SageMath when --sage is given.
"""
import argparse
import csv
import itertools
import subprocess
import sys
from collections import Counter
from pathlib import Path


def read_posts(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
    posts = []
    for r in rows:
        accts = {r["started_by"].strip()} | {c.strip() for c in (r.get("collaborators") or "").split(";") if c.strip()}
        posts.append(dict(code=r["code"], t=r["taken_at_utc"], block=frozenset(accts)))
    posts.sort(key=lambda p: (p["t"], p["code"]))
    return posts


def automorphisms(points, blocks):
    """all permutations of points that carry the multiset of blocks onto itself"""
    target = Counter(blocks)
    r = {p: sum(p in b for b in blocks) for p in points}
    lam = {frozenset(e): sum(set(e) <= b for b in blocks) for e in itertools.combinations(points, 2)}
    size_profile = {p: sorted(len(b) for b in blocks if p in b) for p in points}
    auts = []

    def extend(m):
        if len(m) == len(points):
            if Counter(frozenset(m[x] for x in b) for b in blocks) == target:
                auts.append(dict(m))
            return
        p = points[len(m)]
        for q in points:
            if q in m.values() or r[q] != r[p] or size_profile[q] != size_profile[p]:
                continue
            if all(lam[frozenset((p, x))] == lam[frozenset((q, m[x]))] for x in m):
                m[p] = q
                extend(m)
                del m[p]

    extend({})
    return auts


def orbits(points, auts):
    seen, out = set(), []
    for p in points:
        if p in seen:
            continue
        o = sorted({a[p] for a in auts})
        seen |= set(o)
        out.append(o)
    return out


def sage_order(sage, points, blocks):
    idx = {p: i for i, p in enumerate(points)}
    B = [sorted(idx[p] for p in b) for b in blocks]
    code = f"S = IncidenceStructure({len(points)}, {B}); G = S.automorphism_group(); print(G.order())"
    out = subprocess.run([sage, "-c", code], capture_output=True, text=True)
    return out.stdout.strip() or ("error: " + out.stderr.strip()[-300:])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("posts")
    ap.add_argument("--mark", action="append", default=[], help="CODE=LABEL, e.g. DcR9bobtKcF=B7 (repeatable)")
    ap.add_argument("--sage", help="path to the sage binary, for a cross-check of |Aut|")
    ap.add_argument("--out", help="folder for order.tsv and report.md")
    a = ap.parse_args(argv)
    posts = read_posts(a.posts)
    marks = dict(m.split("=", 1) for m in a.mark)
    for i, p in enumerate(posts, 1):
        p["rank"] = i
        p["label"] = marks.get(p["code"], "")
    points = sorted(set().union(*(p["block"] for p in posts)))
    blocks = [p["block"] for p in posts]
    auts = automorphisms(points, blocks)
    orbs = orbits(points, auts)
    sg = sage_order(a.sage, points, blocks) if a.sage else None

    lines = ["rank\ttaken_at_utc\tcode\tlabel\taccounts"]
    for p in posts:
        lines.append(f"{p['rank']}\t{p['t']}\t{p['code']}\t{p['label']}\t{';'.join(sorted(p['block']))}")
    marked = [p for p in posts if p["label"]]
    md = [f"# Time order and symmetry of {Path(a.posts).name}", "",
          f"{len(posts)} posts (blocks) on {len(points)} accounts (points), in time order.", "",
          f"**|Aut| = {len(auts)}** (plain-Python count)" + (f"; SageMath: **{sg}**" if sg else ""), "",
          "Orbits (accounts that some symmetry swaps): " + "; ".join("{" + ", ".join(o) + "}" for o in orbs if len(o) > 1)
          + (" — every other account fixed" if any(len(o) == 1 for o in orbs) else ""), "",
          "| Marked post | Label | Time (UTC) | Rank among all posts | Rank among marked posts |", "|---|---|---|---|---|"]
    for j, p in enumerate(marked, 1):
        md.append(f"| {p['code']} | {p['label']} | {p['t']} | {p['rank']} of {len(posts)} | {j} of {len(marked)} |")
    md.append("")
    print("\n".join(lines)); print(); print("\n".join(md))
    if a.out:
        o = Path(a.out); o.mkdir(parents=True, exist_ok=True)
        (o / "order.tsv").write_text("\n".join(lines) + "\n"); (o / "report.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
