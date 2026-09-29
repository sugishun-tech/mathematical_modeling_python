#!/usr/bin/env python3
"""Browser checks for the offline HTML; screenshots are evidence, not pixel proofs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=ROOT/'docs')
    parser.add_argument('--report',type=Path,default=ROOT/'reports/visual_checks.json')
    parser.add_argument('--screenshots',type=Path,default=ROOT/'reports/visual')
    parser.add_argument('--no-screenshots',action='store_true')
    args=parser.parse_args()
    args.screenshots.mkdir(parents=True,exist_ok=True)
    results=[]
    paths=sorted(args.directory.glob('*.html'))
    if not paths:
        raise FileNotFoundError(f'No HTML files found in {args.directory}')
    with sync_playwright() as play:
        executable=shutil.which('chromium') or shutil.which('chromium-browser')
        options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if executable:options['executable_path']=executable
        browser=play.chromium.launch(**options)
        for path in paths:
            page=browser.new_page(viewport={'width':1200,'height':1000},device_scale_factor=1)
            external=[];errors=[]
            page.on('request',lambda req:external.append(req.url) if req.url.startswith(('http://','https://')) else None)
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.set_content(path.read_text(), wait_until='load', timeout=45000)
            page.evaluate('''async()=>{await Promise.all([...document.images].map(im=>im.decode().catch(()=>null)));}''')
            measurements=page.evaluate('''()=>({
                images:document.images.length,
                broken_images:[...document.images].filter(im=>!im.complete||im.naturalWidth===0).length,
                math:document.querySelectorAll('[role="math"]').length,
                math_errors:document.querySelectorAll('[data-mml-node="merror"],[data-mjx-error]').length,
                desktop_body_overflow:document.documentElement.scrollWidth>innerWidth+1,
                unresolved_math_placeholders:document.body.innerText.includes('MATHPLACEHOLDER'),
                replacement_characters:document.body.innerText.includes('\\uFFFD')
            })''')
            if not args.no_screenshots:
                page.screenshot(path=str(args.screenshots/(path.stem+'-top.png')))
                math=page.locator('.math-display').first
                if math.count():
                    math.scroll_into_view_if_needed()
                    page.screenshot(path=str(args.screenshots/(path.stem+'-math.png')))
            page.set_viewport_size({'width':760,'height':1000})
            measurements['mobile_body_overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
            measurements.update({'html':path.name,'external_requests':external,'browser_errors':errors})
            measurements['passed']=not(any(measurements[key] for key in [
                'broken_images','math_errors','desktop_body_overflow','mobile_body_overflow',
                'unresolved_math_placeholders','replacement_characters']) or external or errors)
            results.append(measurements)
            print(path.name, 'PASS' if measurements['passed'] else measurements,flush=True)
            page.close()
        browser.close()
    report={'method':'Chromium rendering of the complete HTML string; DOM, image decoding, MathJax error markers, external requests, '
                     'and horizontal overflow at 1200px and 760px; screenshots for manual inspection.',
            'limits':'DOM checks do not prove semantic correctness or the absence of clipped labels inside raster plots. '
                     'See plot contact sheets and manual-review notes.',
            'results':results,'passed':all(row['passed'] for row in results)}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
