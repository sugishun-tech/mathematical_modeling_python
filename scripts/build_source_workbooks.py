#!/usr/bin/env python3
"""Optional private-study source excerpts, built from the user's own fourth-edition PDF.

No PDF, font files or source-page images are required to execute the main course.
This command produces separate, image-backed exercise statements, not solutions.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import re
from pathlib import Path
import unicodedata
import fitz
import nbformat
from PIL import Image, ImageChops, ImageOps

RANGES = {1: (24, 27), 2: (58, 63), 3: (110, 119), 4: (138, 143),
          5: (170, 175), 6: (212, 225), 7: (244, 253), 8: (293, 303), 9: (350, 361)}
COUNTS = {1: 9, 2: 10, 3: 24, 4: 11, 5: 16, 6: 27, 7: 18, 8: 20, 9: 29}
# Supplementary source pages contain diagrams/tables referred to by some prompts.
REFERENCES = {1: [], 2: [], 3: [74, 83, 93, 107], 4: [123, 128, 136],
              5: [146, 151, 156, 165], 6: [178, 185, 201, 206],
              7: [231, 239, 242], 8: [275], 9: [316, 317, 327, 344]}


def find_exercises(doc):
    items, stops = [], {}
    for chapter, (start, end) in RANGES.items():
        stopped = False
        for page_number in range(start, end + 1):
            lines = []
            for block in doc[page_number - 1].get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    text = ''.join(span['text'] for span in line.get('spans', []))
                    lines.append((line['bbox'], text))
            for box, text in sorted(lines, key=lambda value: (value[0][1], value[0][0])):
                if text.strip() == 'Further Reading':
                    stops[chapter] = (page_number, box[1])
                    stopped = True
                    break
                match = re.match(r'^\s*(\d+)\.(?:\s|$)', text)
                if match and 45 < box[0] < 65 and box[1] > 50:
                    items.append({'chapter': chapter, 'number': int(match.group(1)),
                                  'page': page_number, 'y': box[1],
                                  'lead': unicodedata.normalize('NFKC', text)})
            if stopped:
                break
        actual = [item['number'] for item in items if item['chapter'] == chapter]
        if actual != list(range(1, COUNTS[chapter] + 1)):
            raise ValueError(f'Unexpected exercise sequence in chapter {chapter}: {actual}')
        if chapter not in stops:
            raise ValueError(f'Further Reading boundary not found in chapter {chapter}')
    return items, stops


def crop_png(page, top, bottom, zoom=2.8):
    if bottom <= top:
        return None
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                         clip=fitz.Rect(0, top, page.rect.width, bottom), alpha=False)
    image = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    difference = ImageChops.difference(image, Image.new('RGB', image.size, 'white'))
    bounds = difference.getbbox()
    if not bounds:
        return None
    # Keep a border so a tight PDF text box cannot clip a glyph at the raster edge.
    image = ImageOps.expand(image.crop(bounds), border=18, fill='white')
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--chapter', type=int, choices=range(1,10))
    args = parser.parse_args()
    doc = fitz.open(args.pdf)
    if len(doc) != 368:
        raise ValueError('This extraction map targets the supplied 368-page fourth-edition PDF.')
    digest = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    items, stops = find_exercises(doc)
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for chapter in range(1, 10):
        if args.chapter is not None and chapter != args.chapter:
            continue
        existing = args.output / f'{chapter:02d}_source_exercises.ipynb'
        if existing.exists():
            try:
                previous = nbformat.read(existing, 4)
                nbformat.validate(previous)
                if previous.metadata.get('source_pdf_sha256') == digest and previous.metadata.get('exercise_count') == COUNTS[chapter]:
                    print(f'Chapter {chapter}: valid existing workbook retained', flush=True)
                    continue
            except Exception:
                pass
        group = [q for q in items if q['chapter'] == chapter]
        cells = [nbformat.v4.new_markdown_cell(f'''# Chapter {chapter}: source exercise workbook

This workbook preserves the **original English problem statements**, including mathematical notation, tables and diagrams, as embedded high-resolution images. No separate PDF or external image directory is needed to read these statements. The images are source excerpts, not newly authored solutions and not searchable mathematical text.

**Status: statements collected; solutions not implemented or verified.** Use the matching main chapter for model definitions and the shared `modeling` modules for implementation. A problem that references earlier chapters may still require that chapter's material. The supplementary pages at the end help with selected tables and diagrams; they are not a complete reproduction of all cross-referenced exposition.

**Study workflow:** restate the question in your own words; list variables and units; distinguish supplied data from added assumptions; implement the model; compare with an independent calculation; then discuss sensitivity and limitations. Do not mark an exercise solved until all its lettered parts have been addressed.

**Source:** Mark M. Meerschaert, *Mathematical Modeling*, fourth edition (2013), user-supplied PDF. References below use 1-based PDF page numbers. Source excerpts remain textbook material and are **not covered by the repository's MIT license**. Permission to publish these excerpts has not been established. This optional study bundle is kept separate from the code archive.

**Errata:** original source images preserve original printing, including errors. Use `ERRATA.md` in the main project for corrections. In particular, the pig-price units are dollars per pound; farm plot coefficients and truck loading times require corrections; the R/C circuit labels are swapped; and the tracer release is 540 mCi, not 540 Ci.
''')]
        for index, item in enumerate(group):
            end_page, end_y = ((group[index + 1]['page'], group[index + 1]['y'])
                              if index + 1 < len(group) else stops[chapter])
            chunks = []
            for number in range(item['page'], end_page + 1):
                page = doc[number - 1]
                top = max(0, item['y'] - 2.5) if number == item['page'] else 53
                bottom = end_y - 3 if number == end_page else page.rect.height - 24
                content = crop_png(page, top, bottom)
                if content:
                    chunks.append((number, content))
            if not chunks:
                raise ValueError(f'No source image for exercise {chapter}.{item["number"]}')
            attachments, body = {}, []
            for part, (number, content) in enumerate(chunks, 1):
                name = f'ch{chapter:02d}-exercise{item["number"]:02d}-{part}.png'
                attachments[name] = {'image/png': base64.b64encode(content).decode()}
                body.append(f'**Source PDF page {number} (part {part})**\n\n'
                            f'![Original English statement of chapter {chapter}, exercise {item["number"]}, part {part}](attachment:{name})')
            cell = nbformat.v4.new_markdown_cell(
                f'## Exercise {item["number"]}\n\n**Verification status: prompt only.**\n\n' + '\n\n'.join(body),
                attachments=attachments,
                metadata={'exercise_id': f'{chapter}.{item["number"]}',
                          'source_pdf_pages': [n for n, _ in chunks], 'solution_status': 'not_implemented'})
            cells.append(cell)
            cells.append(nbformat.v4.new_markdown_cell('**Your model and verification notes**\n\n'
                'Record your variables, assumptions and equations here. Specify how every subpart will be checked. '
                'Separate analytical reasoning, numerical evidence and any assumptions that cannot be validated from the supplied information.'))
            records.append({'kind': 'exercise', 'id': f'{chapter}.{item["number"]}',
                            'chapter': chapter, 'pdf_pages': [n for n, _ in chunks],
                            'workbook': f'{chapter:02d}_source_exercises.ipynb',
                            'status': 'statement_only_not_solved', 'source_image_parts': len(chunks)})
        if REFERENCES[chapter]:
            cells.append(nbformat.v4.new_markdown_cell('## Selected source references\n\n'
                'These pages provide selected tables, diagrams and model definitions used by the exercises. '
                'They retain the source printing; consult the errata notes before using values or labels.'))
        for number in REFERENCES[chapter]:
            content = crop_png(doc[number - 1], 53, doc[number - 1].rect.height - 24, zoom=2.4)
            name = f'reference-pdf-page-{number}.png'
            cells.append(nbformat.v4.new_markdown_cell(f'### Source PDF page {number}\n\n'
                f'![Supplementary source material, PDF page {number}](attachment:{name})',
                attachments={name: {'image/png': base64.b64encode(content).decode()}}))
        nb = nbformat.v4.new_notebook(cells=cells, metadata={
            'source_pdf_sha256': digest, 'coverage_status': 'source_prompts_only',
            'exercise_count': COUNTS[chapter], 'language_info': {'name': 'python'},
            'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}})
        for i, cell in enumerate(nb.cells):
            cell.id = f'ex{chapter:02d}-{i:03d}'
        nbformat.validate(nb)
        nbformat.write(nb, args.output / f'{chapter:02d}_source_exercises.ipynb')
        print(f'Chapter {chapter}: {COUNTS[chapter]} exercises, {len(cells)} cells', flush=True)
    records = []
    for path in sorted(args.output.glob('*_source_exercises.ipynb')):
        notebook = nbformat.read(path, 4)
        for cell in notebook.cells:
            if cell.metadata.get('exercise_id'):
                key = cell.metadata['exercise_id']
                records.append({'kind': 'exercise', 'id': key, 'chapter': int(key.split('.')[0]),
                                'pdf_pages': list(cell.metadata['source_pdf_pages']), 'workbook': path.name,
                                'status': 'statement_only_not_solved',
                                'source_image_parts': len(cell.get('attachments', {}))})
    (args.output / 'exercise_manifest.json').write_text(json.dumps({
        'source_pdf_sha256': digest, 'exercise_count': len(records), 'items': records}, indent=2))

if __name__ == '__main__':
    main()
