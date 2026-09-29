#!/usr/bin/env python3
"""Export already-executed notebooks to standalone, offline HTML with static SVG math.

Requires Node.js with mathjax-full 3.x, markdown-it-py, and nbformat.
No browser, external fonts, network connection or MathJax CDN is used at read time.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import nbformat
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
CSS = '''
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f4f5f7;color:#20242b;
font:17px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:1060px;margin:0 auto;padding:32px 42px 80px;background:white}
h1{font-size:2.1rem;line-height:1.2;letter-spacing:-.035em;margin-top:20px}h2{font-size:1.48rem;margin-top:54px;padding-top:20px;border-top:1px solid #dce0e5}
h3{font-size:1.12rem;margin-top:25px}a{color:#245a87}p{margin:.8em 0}pre{font:13px/1.6 ui-monospace,Consolas,monospace;overflow-x:auto;white-space:pre;padding:18px;background:#f4f6f8;border:1px solid #e1e5eb;border-radius:5px}
code{font-family:ui-monospace,Consolas,monospace}p code{font-size:.9em;background:#f1f3f5;padding:1px 4px}.code-label{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#616b76;margin-top:22px}.output pre{background:white;border-left:3px solid #d4dbe4}
.output{overflow-x:auto}table{border-collapse:collapse;font-size:13px;line-height:1.5;margin:20px 0}th,td{text-align:right;border-bottom:1px solid #dde1e5;padding:6px 10px}th:first-child,td:first-child{text-align:left}th{font-weight:650;background:#f5f7f9}
figure{margin:24px 0;text-align:center}figure img{max-width:100%;height:auto}figcaption{font-size:12px;color:#65717e}blockquote{margin:20px 0;padding:2px 20px;border-left:3px solid #9aaebf;background:#f7f9fb}
.math-display{max-width:100%;overflow-x:auto;padding:12px 0;text-align:center}.math-inline{display:inline-block;vertical-align:middle;max-width:100%}mjx-container svg{overflow:visible}nav{font-size:13px;border-bottom:1px solid #dde1e5;padding-bottom:16px}footer{margin-top:55px;padding-top:18px;border-top:1px solid #dde1e5;font-size:13px;color:#65717e}
@media(max-width:760px){main{padding:20px 18px 50px}body{font-size:16px}h1{font-size:1.8rem}pre{font-size:12px}th,td{padding:5px 7px}.math-display{font-size:14px}}
@media print{body,main{background:white}main{max-width:none;padding:0}pre{white-space:pre-wrap}h2,h3{break-after:avoid}figure{break-inside:avoid}nav{display:none}}
'''

def node_environment():
    environment = os.environ.copy()
    roots = [str(ROOT / 'node_modules')]
    try:
        roots.append(subprocess.check_output(['npm', 'root', '-g'], text=True, timeout=15).strip())
    except (OSError, subprocess.SubprocessError):
        pass
    if environment.get('NODE_PATH'):
        roots.append(environment['NODE_PATH'])
    environment['NODE_PATH'] = os.pathsep.join(roots)
    return environment


def convert(path, destination):
    nb = nbformat.read(path, 4)
    formulas, parts = [], []
    md = MarkdownIt('commonmark', {'html': True}).enable('table')
    plain_dollars = []
    def placeholder(tex, display):
        index = len(formulas)
        formulas.append({'tex': tex.strip(), 'display': display})
        return f'MATHPLACEHOLDER{index:06d}END'
    def markdown(source, attachments, cell_index):
        # Protect literal code before finding math delimiters.
        protected = []
        def protect(match):
            protected.append(match.group(0))
            return f'CODEPROTECTED{len(protected)-1:06d}END'
        source = re.sub(r'```[\s\S]*?```|`[^`\n]+`', protect, source)
        source = re.sub(r'\$\$([\s\S]+?)\$\$', lambda m: placeholder(m.group(1), True), source)
        source = re.sub(r'\\\[([\s\S]+?)\\\]', lambda m: placeholder(m.group(1), True), source)
        source = re.sub(r'\\\((.+?)\\\)', lambda m: placeholder(m.group(1), False), source)
        source = re.sub(r'(?<![\\$])\$(?!\$)([^\n$]+?)(?<!\\)\$(?!\$)', lambda m: placeholder(m.group(1), False), source)
        if re.search(r'(?<!\\)\$', source):
            plain_dollars.append(cell_index)
        for index, code in enumerate(protected):
            source = source.replace(f'CODEPROTECTED{index:06d}END', code)
        rendered = md.render(source)
        for name, bundle in attachments.items():
            if 'image/png' in bundle:
                rendered = rendered.replace('attachment:' + name, 'data:image/png;base64,' + bundle['image/png'])
        return rendered
    title = next((c.source.splitlines()[0].lstrip('# ') for c in nb.cells if c.cell_type == 'markdown'), path.stem)
    image_count = 0
    for index, cell in enumerate(nb.cells):
        if cell.cell_type == 'markdown':
            parts.append(f'<section id="cell-{index}">'+markdown(cell.source, cell.get('attachments', {}), index)+'</section>')
        elif cell.cell_type == 'code':
            parts.append(f'<div class="code-label">Python · cell {index} · execution {cell.execution_count}</div>')
            parts.append('<pre><code>'+html.escape(cell.source)+'</code></pre>')
            for oi, output in enumerate(cell.get('outputs', [])):
                if output.output_type == 'error':
                    raise ValueError(f'{path}: error output at cell {index}')
                if output.output_type == 'stream':
                    parts.append('<div class="output"><pre>'+html.escape(output.text)+'</pre></div>')
                    continue
                data = output.get('data', {})
                if 'image/png' in data:
                    image_count += 1
                    parts.append(f'<figure><img alt="Computed figure {image_count}, notebook cell {index}" src="data:image/png;base64,'+data['image/png']+f'"><figcaption>Computed figure {image_count} · cell {index}</figcaption></figure>')
                elif 'text/latex' in data:
                    tex = data['text/latex'].strip()
                    if tex.startswith('$$') and tex.endswith('$$'): tex = tex[2:-2]
                    elif tex.startswith('$') and tex.endswith('$'): tex = tex[1:-1]
                    parts.append(placeholder(tex, True))
                elif 'text/html' in data:
                    cleaned = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', data['text/html'], flags=re.I)
                    parts.append('<div class="output">'+cleaned+'</div>')
                elif 'text/plain' in data:
                    parts.append('<div class="output"><pre>'+html.escape(data['text/plain'])+'</pre></div>')
    if plain_dollars:
        raise ValueError(f'{path}: unmatched or ambiguous dollar delimiters in markdown cells {plain_dollars}')
    process = subprocess.run(['node', str(ROOT / 'scripts/mathjax_svg.js')],
                             input=json.dumps(formulas), text=True, capture_output=True,
                             env=node_environment(), timeout=90)
    if process.returncode:
        raise RuntimeError(process.stderr)
    results = json.loads(process.stdout)
    body = '\n'.join(parts)
    for index, (formula, result) in enumerate(zip(formulas, results)):
        if result['error']:
            raise ValueError(f'{path}: formula {index}: {formula["tex"]}: {result["error"]}')
        tag, classname = ('div', 'math-display') if formula['display'] else ('span', 'math-inline')
        svg = f'<{tag} class="{classname}" role="math" aria-label="{html.escape(formula["tex"], quote=True)}">'+result['svg']+f'</{tag}>'
        body = body.replace(f'MATHPLACEHOLDER{index:06d}END', svg)
    # Source attachments are responsive too. They remain images, not typed math.
    body = re.sub(r'<img (?!style=)', '<img style="max-width:100%;height:auto" ', body)
    document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    document += '<title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body><main><nav><a href="index.html">Course index</a> · Offline edition · SVG mathematics</nav>'
    document += body+'<footer>Mathematical Modeling in Python · Original computational companion to Meerschaert (2013). Numerical verification is conditional on the stated models. See COVERAGE.md and ERRATA.md for scope and limitations.</footer></main></body></html>'
    destination.write_text(document)
    return {'notebook': str(path), 'html': destination.name, 'formulas': len(formulas),
            'computed_figures': image_count, 'math_errors': 0, 'unmatched_delimiters': 0,
            'static_math': True, 'external_runtime_assets': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notebooks', type=Path, default=ROOT/'notebooks')
    parser.add_argument('--output', type=Path, default=ROOT/'docs')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted(args.notebooks.glob('*.ipynb')):
        report = convert(path, args.output/(path.stem+'.html'))
        reports.append(report)
        print(f'{path.name}: {report["formulas"]} formulas, {report["computed_figures"]} figures', flush=True)
    links=''.join(f'<tr><td><a href="{html.escape(r["html"])}">{html.escape(Path(r["notebook"]).stem.replace("_"," "))}</a></td><td>{r["formulas"]}</td><td>{r["computed_figures"]}</td></tr>' for r in reports)
    index=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mathematical Modeling in Python</title><style>{CSS}</style><main><h1>Mathematical Modeling<br>in Python</h1><p>Read the problem, formulate a model, inspect the computation, verify the result, and explain what it means.</p><p>This offline edition contains original English statements and computations for all 44 numbered examples. It does not claim to reproduce every source calculation or to solve the 164 end-of-chapter exercises. The separate source exercise study bundle provides their original statements.</p><table><thead><tr><th>Chapter</th><th>Formula renderings</th><th>Computed figures</th></tr></thead><tbody>{links}</tbody></table><h2>Reading and verification</h2><p>No Jupyter kernel, network connection, external font files or MathJax CDN is required to read these pages. Mathematics has been converted to embedded SVG. Run the notebooks to change inputs or repeat the calculations.</p><p>See README.md, COVERAGE.md, ERRATA.md and the reports directory in the project archive for execution instructions, source mapping and limits of the verification.</p></main></html>'''
    (args.output/'index.html').write_text(index)
    (args.output/'render_manifest.json').write_text(json.dumps(reports, indent=2))

if __name__ == '__main__':
    main()
