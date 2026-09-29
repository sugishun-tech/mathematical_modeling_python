#!/usr/bin/env python3
"""Reconcile source identifiers, notebook outputs and provenance without overclaiming."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys
import traceback
import nbformat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
EXPECTED_EXAMPLES=[1,5,7,4,4,6,5,6,6]
EXPECTED_EXERCISES=[9,10,24,11,16,27,18,20,29]

def audit():
    failures=[];books=[];seen=[];assertions=0;figures=0
    try:
        from run_all import validate
    except Exception as exc:
        validate=None;failures.append(f'Runner import: {exc}')
    for path in sorted((ROOT/'notebooks').glob('0*.ipynb')):
        try:
            nb=nbformat.read(path,4);nbformat.validate(nb)
            keys=[c.metadata['textbook_example'] for c in nb.cells if c.metadata.get('textbook_example')]
            seen.extend(keys)
            code=[c for c in nb.cells if c.cell_type=='code']
            for cell in code:
                assertions+=sum(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(cell.source)))
                figures+=sum('image/png' in output.get('data',{}) for output in cell.get('outputs',[]))
            for index,cell in enumerate(nb.cells):
                if re.search('[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]',cell.source):
                    failures.append(f'{path.name} cell {index}: unexpected control/replacement character')
                if cell.metadata.get('textbook_example') and 'problem' not in cell.source.lower():
                    failures.append(f'{path.name}: example {cell.metadata.textbook_example} has no problem label')
            validation=validate(path) if validate is not None else ['runner unavailable']
            if validation:
                failures.extend(f'{path.name}: {issue}' for issue in validation)
            books.append({'notebook':path.name,'examples':keys,'code_cells':len(code),'validation':validation})
        except Exception as exc:
            failures.append(f'{path.name}: {type(exc).__name__}: {exc}')
    expected=[f'{ch}.{ex}' for ch,count in enumerate(EXPECTED_EXAMPLES,1) for ex in range(1,count+1)]
    if len(books)!=9:failures.append(f'Expected 9 main notebooks; parsed {len(books)}')
    if len(seen)!=44 or set(seen)!=set(expected):failures.append('Numbered-example set differs from the expected 44 identifiers')
    inventory_path=ROOT/'reports/source_inventory.json'
    inventory={}
    try:
        inventory=json.loads(inventory_path.read_text())
        records=inventory.get('examples',[])
        if {r['id'] for r in records}!=set(expected):failures.append('Source inventory/example mismatch')
        for item in records:
            if not item.get('pdf_page_range'):failures.append(f'Missing PDF page reference for example {item["id"]}')
        exercises=inventory.get('exercises',[])
        target={f'{ch}.{ex}' for ch,count in enumerate(EXPECTED_EXERCISES,1) for ex in range(1,count+1)}
        if {r['id'] for r in exercises}!=target:failures.append('Source inventory/exercise mismatch')
        if any(r.get('status')!='statement_only_not_solved' for r in exercises):
            failures.append('An exercise status incorrectly implies a verified solution')
    except Exception as exc:failures.append(f'Source inventory: {exc}')
    render_manifest=ROOT/'docs/render_manifest.json'
    rendering={}
    try:
        records=json.loads(render_manifest.read_text())
        rendering={'chapters':len(records),'formula_renderings':sum(r.get('formulas',0) for r in records),
                   'computed_figures':sum(r.get('computed_figures',0) for r in records)}
        if len(records)!=9:failures.append('Expected 9 rendered chapter pages')
        if any(r.get('math_errors',0) or r.get('unmatched_delimiters',0) for r in records):
            failures.append('A math export reported errors')
    except Exception as exc:failures.append(f'HTML export manifest: {exc}')
    try:
        visual=json.loads((ROOT/'reports/visual_checks.json').read_text())
        if not visual.get('passed'):failures.append('Browser rendering checks did not all pass')
    except Exception as exc:failures.append(f'Browser report: {exc}')
    report={'scope':'Structural checks, recorded execution provenance, source-ID reconciliation and browser report. '
                    'This is not a complete mathematical verification of the textbook.',
            'main_notebooks':books,'example_count':len(seen),'assertion_statements':assertions,
            'stored_raster_figures':figures,'exercise_solutions_implemented':0,
            'rendering':rendering,'failures':failures,'passed':not failures,
            'manual_visual_review':'No manual-review claim is inferred from the automated checks.'}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/project_audit.json').write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps({'passed':report['passed'],'examples':len(seen),'figures':figures,'failures':failures},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(audit())
