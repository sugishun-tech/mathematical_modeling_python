#!/usr/bin/env python3
"""Execute notebooks in separate clean kernels; validate outputs and provenance."""
from __future__ import annotations
import argparse,hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent

def source_hash(nb):
    data=[{'cell_type':c.cell_type,'source':c.source} for c in nb.cells]
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def dependency_hash():
    digest=hashlib.sha256()
    for path in sorted((ROOT/'modeling').glob('*.py'))+sorted((ROOT/'data').glob('*.csv')):
        digest.update(str(path.relative_to(ROOT)).encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def validate(path,require_execution=True):
    nb=nbformat.read(path,as_version=4);nbformat.validate(nb);issues=[];count=0
    for i,c in enumerate(nb.cells):
        if c.cell_type!='code' or not c.source.strip():continue
        count+=1
        if require_execution and c.execution_count is None:issues.append(f'cell {i}: unexecuted')
        for out in c.get('outputs',[]):
            if out.output_type=='error':issues.append(f"cell {i}: {out.get('ename')}: {out.get('evalue')}")
            if out.output_type=='stream' and re.search(r'RuntimeWarning|Glyph .* missing|overflow encountered|invalid value encountered',out.get('text','')):
                issues.append(f'cell {i}: numerical/rendering warning: {out.text[:200]}')
    if require_execution and count:
        v=nb.metadata.get('verification',{})
        if v.get('source_sha256')!=source_hash(nb):issues.append('outputs missing provenance or stale against source')
        if v.get('dependency_sha256')!=dependency_hash():issues.append('outputs stale against modules/data')
    return issues

def execute(path,timeout):
    nb=nbformat.read(path,as_version=4);nbformat.validate(nb);started=time.perf_counter()
    NotebookClient(nb,timeout=timeout,kernel_name='python3',allow_errors=False,
                   resources={'metadata':{'path':str(ROOT)}}).execute()
    nb.metadata['verification']={'source_sha256':source_hash(nb),'dependency_sha256':dependency_hash(),
                                 'executed_utc':datetime.now(timezone.utc).isoformat(),'fresh_kernel':True}
    temp=path.with_suffix('.tmp.ipynb');nbformat.write(nb,temp);issues=validate(temp)
    if issues:
        temp.unlink(missing_ok=True);raise RuntimeError('; '.join(issues))
    temp.replace(path)
    outputs=[o for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[])]
    return {'notebook':str(path.relative_to(ROOT)),'status':'passed','seconds':round(time.perf_counter()-started,3),
            'code_cells':sum(c.cell_type=='code' for c in nb.cells),'png_outputs':sum('image/png' in o.get('data',{}) for o in outputs),
            'source_sha256':source_hash(nb)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pattern',default='*.ipynb');p.add_argument('--timeout',type=int,default=600);p.add_argument('--validate-only',action='store_true');args=p.parse_args()
    paths=sorted((ROOT/'notebooks').glob(args.pattern))
    if not paths:print('No notebooks matched',file=sys.stderr);return 2
    report=[]
    for path in paths:
        print(('CHECK ' if args.validate_only else 'RUN   ')+path.name,flush=True)
        try:
            if args.validate_only:
                issues=validate(path)
                if issues:raise RuntimeError('; '.join(issues))
                result={'notebook':str(path.relative_to(ROOT)),'status':'passed'}
            else:result=execute(path,args.timeout)
            report.append(result);print('PASS  '+path.name,flush=True)
        except Exception as error:
            report.append({'notebook':str(path.relative_to(ROOT)),'status':'failed','error':str(error)})
            print('FAIL  '+path.name+'\n'+str(error),file=sys.stderr,flush=True)
    folder=ROOT/'reports';folder.mkdir(exist_ok=True)
    name='validation.json' if args.validate_only else 'execution.json'
    old=[]
    if (folder/name).exists():old=json.loads((folder/name).read_text()).get('results',[])
    replaced={r['notebook'] for r in report};combined=[r for r in old if r['notebook'] not in replaced]+report
    (folder/name).write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'results':sorted(combined,key=lambda r:r['notebook'])},indent=2))
    return int(any(r['status']!='passed' for r in report))
if __name__=='__main__':raise SystemExit(main())
