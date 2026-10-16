#!/usr/bin/env python3
"""
Build the Study 5 analysis dataset from the Qualtrics exports.

Why this exists. The numeric export stores raw Qualtrics choice IDs, not 1-to-k
recodes, and the IDs differ item by item (a "Highly transformative" response is
14 on one item and 26 on another). Scale position therefore has to be rebuilt
from the label export against each item's ChoiceOrder in the .qsf. Two of the
thirty transformativeness items also carry a six-point scale, so the number of
scale points is carried per row rather than assumed.

Source time is not recoverable. Study 5's image-slot recorder reads
${e://Field/ArtistHr}, which the flow never sets (it sets ArtistHr_Source), so
every Image{k}_Time is blank. The vignette piped the correct field, so the
manipulation was seen; only the trial-level mapping is lost. The assignment
script enforced two trials per level, so source time is balanced 2/2/2 within
each participant by construction and enters no model here.

Outputs, all under Analysis/R Analysis Pipeline/Study 5/:
  tables/study5_exclusion_flow.csv   participant flow, one row per step
  tables/study5_cell_counts.csv      Type x ArtistHr_Derivative counts
  tables/study5_item_scales.csv      every rating item, its anchors, its k
  study5_wide.csv                    one row per retained participant
  study5_long.csv                    one row per participant x image x
                                     modification x dimension
"""
import csv, json, re, os, sys, collections

# The project root is found from this file's own folder. The file sits in
# <root>/Analysis/R Analysis Pipeline/Study 5/, so the root is three folders
# up. Setting the environment variable STUDY5_PROJECT_ROOT gives the root
# instead, for a copy of the project kept somewhere else. The message on
# failure says where the root came from and does not print it, so that it
# names no account and no folder particular to one machine.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = (os.environ.get("STUDY5_PROJECT_ROOT")
        or os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir)))
if not (os.path.isdir(os.path.join(ROOT, "Data"))
        and os.path.isdir(os.path.join(ROOT, "Analysis"))):
    where = ("The folder STUDY5_PROJECT_ROOT names" if os.environ.get("STUDY5_PROJECT_ROOT")
             else "The folder three levels above this file")
    sys.exit(where + " has no Data and Analysis folders."
             "\nSet STUDY5_PROJECT_ROOT to the folder that holds them.")
QSF  = os.path.join(ROOT, "Analysis/R Analysis Pipeline/Study 5/Final_-_AI_Copyright_-_Study_5.qsf")
VALS = os.path.join(ROOT, "Data/Study 5/Study5_Values.csv")
LABS = os.path.join(ROOT, "Data/Study 5/Study5_Labels.csv")
OUT  = os.path.join(ROOT, "Analysis/R Analysis Pipeline/Study 5")

RATE_RE = re.compile(r'^(\d)(Figure|NonFigure)(None|Min|Max)(Trans|Ess|Creat)$')

def clean(s):
    if not s: return ""
    s = re.sub(r'<[^>]+>', ' ', s)
    for a, b in [('&nbsp;',' '),('&amp;','&'),('&quot;','"'),('&#39;',"'"),
                 ('&rsquo;',"'"),('&ldquo;','"'),('&rdquo;','"'),('&lsquo;',"'")]:
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s).strip()

# ---------------------------------------------------------------- scale keys
def item_scales(qsf_path):
    d = json.load(open(qsf_path))
    # Questions in the survey's Trash block were deleted before launch. The
    # .qsf still holds them, and one of them (QID28) carries the export tag
    # 1FigureMaxCreat of a live question, so they are left out here.
    trash = set()
    for e in d['SurveyElements']:
        if e['Element'] != 'BL':
            continue
        blocks = e['Payload'].values() if isinstance(e['Payload'], dict) else e['Payload']
        for b in blocks:
            if b.get('Type') == 'Trash':
                trash |= {x['QuestionID'] for x in b.get('BlockElements', [])
                          if x.get('Type') == 'Question'}
    out = {}
    for e in d['SurveyElements']:
        if e['Element'] != 'SQ':
            continue
        p = e['Payload']
        tag = p.get('DataExportTag') or ''
        ch = p.get('Choices')
        if not RATE_RE.match(tag) or not isinstance(ch, dict):
            continue
        if p.get('QuestionID') in trash:
            continue
        assert tag not in out, f"{tag}: more than one live question carries this export tag"
        order = p.get('ChoiceOrder') or list(ch.keys())
        labels = [clean(ch[str(k)].get('Display')) for k in order if str(k) in ch]
        out[tag] = {'labels': labels,
                    'k': len(labels),
                    'stem': clean(p.get('QuestionText'))}
    return out

# ------------------------------------------------------------------ loading
def load(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    hdr = rows[0]
    return hdr, [dict(zip(hdr, r)) for r in rows[3:]]   # drop the two metadata rows

def main():
    scales = item_scales(QSF)
    hv, dv = load(VALS)
    hl, dl = load(LABS)
    assert len(dv) == len(dl), "value and label exports differ in length"

    rate_cols = sorted([h for h in hv if RATE_RE.match(h)])
    missing = [c for c in rate_cols if c not in scales]
    if missing:
        print("WARNING: no scale key for", missing, file=sys.stderr)

    # Each rating item has one justification column: the item's name followed
    # by "Resp" (1FigureNoneCreatResp), "Re" (1NonFigureMaxCreatRe) or "R"
    # (1NonFigureNoneCreatR), depending on the item. The column is looked up
    # once per item in the header of the label export, and the build stops if
    # an item has no such column or more than one.
    just_col = {}
    for c in rate_cols:
        found = [c + s for s in ('Resp', 'Re', 'R') if c + s in hl]
        assert len(found) == 1, f"{c}: expected one justification column, found {found}"
        just_col[c] = found[0]

    # -------------------------------------------------------------- screening
    flow, kept = [], list(zip(dv, dl))
    flow.append(("0. records in export", len(kept)))
    kept = [(a, b) for a, b in kept if a.get('Status') == '0']
    flow.append(("1. survey previews removed (Status = IP Address)", len(kept)))
    kept = [(a, b) for a, b in kept if a.get('Finished') == '1']
    flow.append(("2. finished", len(kept)))
    kept = [(a, b) for a, b in kept if b.get('Seriousness') == 'Yes, I did']
    flow.append(("3. self-reported serious completion", len(kept)))
    kept = [(a, b) for a, b in kept
            if (a.get('AttentionCheck2') or '').strip() == '' or b.get('AttentionCheck2') == '15']
    flow.append(("4. arithmetic check correct where answered", len(kept)))
    kept = [(a, b) for a, b in kept if a.get('Type') and a.get('ArtistHr_Derivative')]
    flow.append(("5. condition assignment recorded", len(kept)))

    # a participant should carry 54 ratings: 6 images x 3 levels x 3 dimensions
    def nrat(a): return sum(1 for c in rate_cols if (a.get(c) or '').strip())
    kept_full = [(a, b) for a, b in kept if nrat(a) == 54]
    flow.append(("6. complete trial data (54 ratings)", len(kept_full)))

    with open(os.path.join(OUT, "tables/study5_exclusion_flow.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["step", "n"]); w.writerows(flow)
    for s, n in flow: print(f"  {s:<50s} {n}")

    partial = [(a, b) for a, b in kept if nrat(a) != 54]
    if partial:
        print("\n  participants retained at step 5 with other than 54 ratings:")
        for a, b in partial:
            print(f"    {a['ResponseId']}  n_ratings={nrat(a)}  Type={a['Type']}  deriv={a['ArtistHr_Derivative']}")

    analytic = kept_full

    # ------------------------------------------------------------ cell counts
    cells = collections.Counter((a['Type'], a['ArtistHr_Derivative']) for a, b in analytic)
    with open(os.path.join(OUT, "tables/study5_cell_counts.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Type", "ArtistHr_Derivative", "n"])
        for (t, h), n in sorted(cells.items()): w.writerow([t, h, n])
    print("\n  cells (Type x derivative effort):")
    for (t, h), n in sorted(cells.items()): print(f"    {t:<6s} {h:<17s} {n}")

    # ------------------------------------------------------------- item table
    with open(os.path.join(OUT, "tables/study5_item_scales.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "image", "stimulus_type", "modification", "dimension",
                    "k_points", "anchors", "stem"])
        for c in rate_cols:
            m = RATE_RE.match(c); s = scales.get(c, {})
            w.writerow([c, m.group(1), m.group(2), m.group(3), m.group(4),
                        s.get('k', ''), " | ".join(s.get('labels', [])), s.get('stem', '')])

    # ------------------------------------------------------------------ long
    dim_name = {'Trans': 'transformativeness', 'Ess': 'essence_change', 'Creat': 'creativity'}
    mod_name = {'None': 'None', 'Min': 'Slight', 'Max': 'Dramatic'}
    long_rows = []
    for a, b in analytic:
        pid = a['ResponseId']
        order = {}
        for k in range(1, 7):
            nm = (a.get(f'Image{k}') or '').strip()
            if nm: order[nm] = k
        for c in rate_cols:
            raw = (a.get(c) or '').strip()
            if not raw: continue
            m = RATE_RE.match(c)
            img, st, mod, dim = m.groups()
            lab = (b.get(c) or '').strip()
            key = scales.get(c, {})
            labels = key.get('labels', [])
            pos = labels.index(lab) + 1 if lab in labels else ''
            block = f"Image{img}_{'Figure' if st=='Figure' else 'Nonfigure'}"
            long_rows.append({
                'id': pid,
                'Type': a['Type'],
                'deriv_effort': a['ArtistHr_Derivative'],
                'stimulus_id': f"{img}{st}",
                'stimulus_type': 'Figure' if st == 'Figure' else 'NonFigure',
                'modification': mod_name[mod],
                'dimension': dim_name[dim],
                'item': c,
                'rating': pos,
                'k_points': key.get('k', ''),
                'rating_label': lab,
                'raw_choice_id': raw,
                'presentation_position': order.get(block, ''),
                'justification': (b.get(just_col[c]) or '').strip(),
                'age': a.get('Age', ''), 'gender': b.get('Gender', ''),
                'experience': b.get('Experience', ''),
            })

    # Every retained participant gave 54 ratings (step 6 of the flow), and
    # every rating should carry its written justification.
    n_just = collections.Counter(r['id'] for r in long_rows if r['justification'])
    short = {a['ResponseId']: n_just[a['ResponseId']] for a, b in analytic
             if n_just[a['ResponseId']] != 54}
    assert not short, f"participants without 54 non-empty justifications: {short}"

    fields = list(long_rows[0].keys())
    with open(os.path.join(OUT, "study5_long.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(long_rows)

    # ------------------------------------------------------------------ wide
    keep_meta = ['ResponseId', 'Type', 'ArtistHr_Derivative', 'Duration (in seconds)',
                 'Finished', 'RecordedDate', 'Age'] + [f'Image{k}' for k in range(1, 7)]
    with open(os.path.join(OUT, "study5_wide.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keep_meta + ['Gender', 'Race', 'Language', 'Experience'] + rate_cols)
        for a, b in analytic:
            w.writerow([a.get(c, '') for c in keep_meta] +
                       [b.get(c, '') for c in ('Gender', 'Race', 'Language', 'Experience')] +
                       [a.get(c, '') for c in rate_cols])

    six = [c for c in rate_cols if scales.get(c, {}).get('k') == 6]
    print(f"\n  long rows: {len(long_rows)}   participants: {len(analytic)}")
    print(f"  six-point items: {six}")
    n6 = sum(1 for r in long_rows if r['k_points'] == 6)
    print(f"  observations on a six-point scale: {n6} of {len(long_rows)}")
    unresolved = sum(1 for r in long_rows if r['rating'] == '')
    print(f"  ratings whose label did not match a choice order: {unresolved}")
    nojust = sum(1 for r in long_rows if not r['justification'])
    print(f"  observations with no justification text: {nojust}")

if __name__ == '__main__':
    main()
