#!/usr/bin/env node
/* Convert formula strings into self-contained SVG paths. No font files are exported. */
'use strict';
const fs = require('fs');
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const document = mathjax.document('', {
  InputJax: new TeX({packages: AllPackages}),
  OutputJax: new SVG({fontCache: 'none'})
});
const formulas = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = formulas.map((item) => {
  try {
    const node = document.convert(item.tex, {display: item.display});
    const svg = adaptor.outerHTML(node);
    return {svg, error: /data-mjx-error|data-mml-node="merror"/.test(svg) ? 'MathJax error' : null};
  } catch (error) {
    return {svg: '', error: String(error)};
  }
});
process.stdout.write(JSON.stringify(output));
