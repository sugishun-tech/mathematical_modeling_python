from pathlib import Path
import json,re,hashlib,csv,fitz,nbformat
from collections import defaultdict
import argparse
parser = argparse.ArgumentParser(description="Rebuild source-ID inventory and transcribe Table 8.1 from the matching supplied PDF.")
parser.add_argument("--pdf", required=True, type=Path)
parser.add_argument("--workbooks", type=Path, help="Optional source exercise notebook directory; default notebooks/exercises")
args = parser.parse_args()
R = Path(__file__).resolve().parents[1]
pdf = args.pdf
workbooks = args.workbooks or R / "notebooks" / "exercises"
doc = fitz.open(pdf)
if len(doc) != 368:
    raise ValueError("This source-page map requires the supplied 368-page fourth-edition PDF.")
# Table 8.1: native text extraction, not OCR; cross-check every CM1 value against
# the project's original data and preserve all six series for future exercises.
rows=[]
for line in doc[274].get_text(sort=True).splitlines():
    m=re.match(r'\s*(\d{1,2})/(\d{2})\s+((?:\d+\.\d+\s*){6})$',line)
    if m:
        values=m.group(3).split();rows.append([f'19{m.group(2)}-{int(m.group(1)):02}',len(rows)+1,*values])
assert len(rows)==37,len(rows)
with (R/'data/mortgage_indices.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['month','t','tb3','tb6','cm1','cm2','cm3','cm5']);w.writerows(rows)
import pandas as pd, numpy as np
original=pd.read_csv(R/'data/cm1.csv');full=pd.read_csv(R/'data/mortgage_indices.csv')
assert np.array_equal(original.cm1,full.cm1) and original.month.equals(full.month)
# Caption labels are recorded as source inventory, not as individually verified results.
source=defaultdict(lambda:defaultdict(list))
for i,page in enumerate(doc):
    text=page.get_text()
    for kind,pattern in [('figure',r'^Figure\s+(\d+\.\d+)\s*:'),('table',r'^Table\s+(\d+\.\d+)\s*:')]:
        for m in re.finditer(pattern,text,re.M):source[kind][m.group(1)].append(i+1)
    for m in re.finditer(r'^\s*\((\d+\.\d+)\)\s*$',text,re.M):source['equation'][m.group(1)].append(i+1)
items=[]
for kind,group in source.items():
    for key,pages in sorted(group.items(),key=lambda it:tuple(map(int,it[0].split('.')))):
        items.append({'kind':kind,'id':key,'pdf_pages':sorted(set(pages)),
                      'status':'source_label_located_not_individually_verified',
                      'note':'Automatic label inventory; repeated references can occur. It is not a completeness proof.'})
examples=[]
for p in sorted((R/'notebooks').glob('*.ipynb')):
    nb=nbformat.read(p,4)
    for cell in nb.cells:
        key=cell.metadata.get('textbook_example')
        if key:
            page_match=re.search(r'PDF (?:pages|pp\.)\s+([\d–—-]+)',cell.source)
            title=cell.source.splitlines()[0].split(': ',1)[-1]
            examples.append({'kind':'example','id':key,'chapter':int(key.split('.')[0]),
                             'title':title,'pdf_page_range':page_match.group(1) if page_match else None,
                             'notebook':str(p.relative_to(R)),'cell_id':cell.id,
                             'status':'implemented_with_checks_execution_report_required',
                             'scope':'central model only; not every printed sub-analysis or figure'})
assert len(examples)==44
exercise=json.loads((workbooks/'exercise_manifest.json').read_text())
assert exercise['exercise_count']==164
sections={1:['The five-step method','Sensitivity analysis','Sensitivity and robustness'],
2:['Unconstrained optimization','Lagrange multipliers','Sensitivity analysis and shadow prices'],
3:['One-variable optimization','Multivariable optimization','Linear programming','Discrete optimization'],
4:['Steady-state analysis','Dynamical systems','Discrete-time models'],
5:['Continuous-time models','Discrete-time models','Phase portraits'],
6:['Discrete-time simulation','Continuous-time simulation','The Euler method','Chaos and fractals'],
7:['Discrete probability','Continuous probability','Introduction to statistics','Diffusion'],
8:['Markov chains','Markov processes','Linear regression','Time series'],
9:['Monte Carlo simulation','The Markov property','Analytic simulation','Particle tracking','Fractional diffusion']}
section_items=[{'kind':'section','id':f'{c}.{i}','title':title,'chapter':c,'status':'topic_present_not_exhaustively_reproduced'} for c,titles in sections.items() for i,title in enumerate(titles,1)]
assert len(section_items)==33
manifest={'source':{'title':'Mathematical Modeling, fourth edition','author':'Mark M. Meerschaert','year':2013,
                   'pdf_pages':len(doc),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
                   'page_convention':'1-based file pages, not printed page labels'},
          'counts':{'instructional_sections':33,'numbered_examples':44,'numbered_exercises':164,
                    **{f'{kind}_labels_detected':len(group) for kind,group in source.items()}},
          'limits':'All numbered examples and end-exercise identifiers were reconciled. '
                   'Equations/figures/tables below are an automatic label inventory, not exhaustive independent verification. '
                   'Worked notebooks cover central models; exercise statements are not solutions.',
          'sections':section_items,'examples':examples,'exercises':exercise['items'],'other_source_labels':items}
(R/'reports/source_inventory.json').write_text(json.dumps(manifest,indent=2))
with (R/'reports/coverage.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['kind','id','chapter','pdf_pages_or_range','location','status'])
    for e in examples:w.writerow(['example',e['id'],e['chapter'],e['pdf_page_range'],e['notebook'],e['status']])
    for e in exercise['items']:w.writerow(['exercise',e['id'],e['chapter'],' '.join(map(str,e['pdf_pages'])),'Optional study bundle: '+e['workbook'],e['status']])
    for e in items:w.writerow([e['kind'],e['id'],e['id'].split('.')[0],' '.join(map(str,e['pdf_pages'])),'Source PDF',e['status']])
print(json.dumps(manifest['counts'],indent=2))
# Review renders for source table and representative exercise boundaries.
# Source-page images are deliberately not copied into the code-only project.
