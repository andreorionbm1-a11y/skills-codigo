#!/usr/bin/env python3
"""Verificador de maquetación: dibuja un HTML/SVG y detecta choques.

Uso:
  python3 verificar.py archivo.html [--ancho 900] [--alto 0] [--pdf] [--salida carpeta]

--ancho   ancho del lienzo en px (A4 vertical ≈ 794; diapositiva 16:9 = 1280)
--alto    alto fijo del lienzo (diapositivas: 720); 0 = página completa
--pdf     además imprime a PDF (respeta saltos de página) y rasteriza cada página
Devuelve código 1 si hay problemas. Siempre deja PNG(s) para revisión visual.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const out = [];
  const vis = el => { const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0.05; };
  const name = el => {
    const t = (el.textContent || '').trim().replace(/\s+/g,' ').slice(0,30);
    return `<${el.tagName.toLowerCase()}${el.className && typeof el.className==='string' ? '.'+el.className.split(' ')[0] : ''}> "${t}"`;
  };
  const items = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement;
    if (!el || !vis(el) || ['SCRIPT','STYLE','TITLE'].includes(el.tagName)) continue;
    if (el.closest('.katex')) continue;                // las fórmulas se evalúan como una sola caja (abajo)
    const r = document.createRange(); r.selectNodeContents(n);
    for (const b of r.getClientRects()) if (b.width > 1 && b.height > 1)
      items.push({el, b, fs: parseFloat(getComputedStyle(el).fontSize)});
  }
  for (const k of document.querySelectorAll('.katex-html')) {
    if (!vis(k)) continue; const b = k.getBoundingClientRect();
    if (b.width > 1 && b.height > 1) items.push({el: k.closest('.katex'), b, fs: parseFloat(getComputedStyle(k).fontSize), mat: true});
  }
  const inter = (a,b) => Math.max(0, Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                         Math.max(0, Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
  // 1. Texto encimado sobre texto
  for (let i=0;i<items.length;i++) for (let j=i+1;j<items.length;j++) {
    const A=items[i], B=items[j]; if (A.el===B.el) continue;
    const a = inter(A.b,B.b), m = Math.min(A.b.width*A.b.height, B.b.width*B.b.height);
    if (a > 4 && a/m > 0.12) out.push({tipo:'TEXTO ENCIMADO', detalle:`${name(A.el)} choca con ${name(B.el)}`,
      zona:[Math.round(A.b.left),Math.round(A.b.top)]});
  }
  // 2. Texto (y su subrayado) fuera de su contenedor con borde/fondo
  const boxed = el => { const s=getComputedStyle(el);
    return parseFloat(s.borderTopWidth)+parseFloat(s.borderBottomWidth)+parseFloat(s.borderLeftWidth) > 0 ||
      (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent'); };
  for (const it of items) {
    let deco = 0;
    for (let q = it.el; q && q!==document.body; q=q.parentElement) {
      const s = getComputedStyle(q);
      if (s.textDecorationLine.includes('underline')) { deco = Math.max(deco, it.fs*0.35); }
      if (q.tagName==='SPAN' && parseFloat(s.borderBottomWidth)>0 && !parseFloat(s.borderTopWidth))
        deco = Math.max(deco, parseFloat(s.paddingBottom)+parseFloat(s.borderBottomWidth)+1);
    }
    let p = it.el;
    const lineOnly = e => { const s=getComputedStyle(e); return parseFloat(s.borderBottomWidth)>0 && !parseFloat(s.borderTopWidth) && s.backgroundColor==='rgba(0, 0, 0, 0)'; };
    while (p && p!==document.body && (!boxed(p) || lineOnly(p))) p = p.parentElement;
    if (!p || p===document.body) continue;
    const c = p.getBoundingClientRect(), s = getComputedStyle(p);
    const inner = {left:c.left+parseFloat(s.borderLeftWidth), right:c.right-parseFloat(s.borderRightWidth),
                   top:c.top+parseFloat(s.borderTopWidth), bottom:c.bottom-parseFloat(s.borderBottomWidth)};
    const b = it.b, tol = 1, bot = b.bottom+deco;
    let fuera = b.left < inner.left-tol || b.right > inner.right+tol || b.top < inner.top-tol || bot > inner.bottom+tol;
    const rad = parseFloat(s.borderTopLeftRadius);
    if (!fuera && rad >= Math.min(c.width,c.height)*0.4) {
      const cx=(inner.left+inner.right)/2, cy=(inner.top+inner.bottom)/2, rx=(inner.right-inner.left)/2, ry=(inner.bottom-inner.top)/2;
      const pts=[[b.left+2,b.top+2],[b.right-2,b.top+2],[b.left+2,bot-1],[b.right-2,bot-1]];
      fuera = pts.some(([x,y]) => ((x-cx)/rx)**2+((y-cy)/ry)**2 > 1.02);
    }
    if (fuera) out.push({tipo: deco ? 'TEXTO O SUBRAYADO TOCA/SALE DEL BORDE' : 'TEXTO SE SALE DEL CONTENEDOR',
        detalle:`${name(it.el)} dentro de ${name(p)}`, zona:[Math.round(b.left),Math.round(b.top)]});
  }
  // 3. Desbordamientos y elementos fuera del lienzo
  const W = document.documentElement.clientWidth;
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el) || el.closest('svg') && el.tagName!=='svg' || el.closest('.katex')) continue;
    const s = getComputedStyle(el);
    if (s.overflow==='visible' && el.scrollWidth > el.clientWidth+2 && el.clientWidth>0 && !['SPAN','A','B','I','EM','STRONG'].includes(el.tagName))
      out.push({tipo:'DESBORDAMIENTO', detalle:`${name(el)} (${el.scrollWidth}px en ${el.clientWidth}px)`});
    const r = el.getBoundingClientRect();
    if (r.width>0 && (r.right > W+1 || r.left < -1)) out.push({tipo:'FUERA DEL LIENZO', detalle:name(el)});
  }
  // 4. Letra demasiado chica
  for (const it of items) if (!it.mat && it.fs < 10) out.push({tipo:'LETRA < 10px', detalle:name(it.el)});
  // 5. SVG: líneas/flechas que atraviesan texto
  for (const g of document.querySelectorAll('svg line, svg path, svg polyline')) {
    if (!vis(g) || !g.getTotalLength || g.closest('.katex') || g.closest('.relleno')) continue;   // .relleno = textura de un área, no una línea
    let L; try { L = g.getTotalLength(); } catch(e) { continue; }
    if (!L) continue;
    const m = g.getScreenCTM(); if (!m) continue;
    const hit = new Set();
    for (let d=0, paso=Math.max(3, L/1500); d<=L; d+=paso) {
      const pt = g.getPointAtLength(d), x = pt.x*m.a+pt.y*m.c+m.e, y = pt.x*m.b+pt.y*m.d+m.f;
      for (const it of items) { const b=it.b;
        if (x>b.left+1 && x<b.right-1 && y>b.top+2 && y<b.bottom-2) hit.add(it.el); }
    }
    for (const el of hit) out.push({tipo:'LÍNEA CRUZA TEXTO', detalle:`${name(g)} atraviesa ${name(el)}`});
  }
  // 6. SVG: texto que queda a medias dentro de una figura (no cabe en su caja)
  const shapes = [...document.querySelectorAll('svg rect, svg circle, svg ellipse, svg polygon')].filter(e => vis(e) && !e.closest('.katex'));
  for (const it of items) { if (!it.el.closest('svg')) continue;
    for (const sh of shapes) { const c = sh.getBoundingClientRect(), b = it.b;
      const a = inter(b,c), t = b.width*b.height;
      if (sh.tagName !== 'rect' && a > 2 && c.width*c.height > t*0.8) {
        // formas no rectangulares: probar la forma real, no su caja
        const m = sh.getScreenCTM(), sv = sh.ownerSVGElement; if (!m || !sv) continue;
        let n = 0; const mi = m.inverse();
        for (const fx of [.1,.5,.9]) for (const fy of [.2,.5,.8]) { const p = sv.createSVGPoint();
          p.x = b.left + b.width*fx; p.y = b.top + b.height*fy; if (sh.isPointInFill(p.matrixTransform(mi))) n++; }
        if (n > 0 && n < 9) out.push({tipo:'TEXTO NO CABE EN LA FIGURA', detalle:`${name(it.el)} a medias en <${sh.tagName}>`});
        continue; }
      if (c.width*c.height > t*0.8 && a > 2 && a < t*0.97)
        out.push({tipo:'TEXTO NO CABE EN LA FIGURA', detalle:`${name(it.el)} en <${sh.tagName}> (${Math.round(b.width)}px de texto, ${Math.round(c.width)}px de figura)`});
    } }
  // 7. Contraste de texto contra su fondo real (WCAG: 4.5, o 3 si es grande)
  const rgb = s => { const m = (s||'').match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const v = m[1].split(/[ ,/]+/).filter(Boolean).map(parseFloat); return {r:v[0],g:v[1],b:v[2],a:v.length>3?v[3]:1}; };
  const L = c => { const f = x => { x/=255; return x<=0.03928 ? x/12.92 : ((x+0.055)/1.055)**2.4; };
    return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b); };
  const fondoHTML = el => { for (let q=el; q; q=q.parentElement) { const c = rgb(getComputedStyle(q).backgroundColor);
      if (c && c.a > 0.5) return c; } return {r:255,g:255,b:255,a:1}; };
  const vistos = new Set();
  for (const it of items) {
    if (vistos.has(it.el)) continue; vistos.add(it.el);
    if (it.mat) continue;
    const s = getComputedStyle(it.el), enSvg = !!it.el.closest('svg');
    const tinta = rgb(enSvg ? s.fill : s.color); if (!tinta || tinta.a < 0.5) continue;
    let fondo = null;
    if (enSvg) {
      const x = (it.b.left+it.b.right)/2, y = (it.b.top+it.b.bottom)/2;
      for (const e of document.elementsFromPoint(x, y)) {
        if (e === it.el || e.closest('text') || e.closest('.katex') || e.closest('foreignObject') || !e.closest('svg') || e.tagName==='svg') continue;
        const f = rgb(getComputedStyle(e).fill), op = parseFloat(getComputedStyle(e).fillOpacity);
        if (f && f.a > 0.5 && op > 0.5) { fondo = f; break; }
      }
    }
    fondo = fondo || fondoHTML(it.el.closest('svg') || it.el);
    const a = L(tinta), b = L(fondo), cr = (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);
    const grande = it.fs >= 24 || (it.fs >= 18.6 && parseInt(s.fontWeight) >= 600);
    if (cr < (grande ? 3 : 4.5)) out.push({tipo:'CONTRASTE BAJO', detalle:`${name(it.el)} tiene contraste ${cr.toFixed(1)} (mínimo ${grande?3:4.5})`});
  }
  // 8. Simetría óptica de fondos (marcatexto, etiquetas, botones): relleno visible arriba ≈ abajo
  const cv = document.createElement('canvas').getContext('2d');
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el) || el.closest('svg') || el.closest('.katex')) continue;
    const s = getComputedStyle(el), bg = rgb(s.backgroundColor);
    if (!bg || bg.a < 0.5) continue;
    const txt = [...el.childNodes].filter(x => x.nodeType===3).map(x => x.textContent).join('').trim();
    if (!txt) continue;
    const r = el.getBoundingClientRect(), fs = parseFloat(s.fontSize);
    if (r.height > fs*3.2) continue;                 // solo etiquetas o títulos de una línea
    const mark = document.createElement('span');
    mark.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    el.appendChild(mark); const base = mark.getBoundingClientRect().bottom; mark.remove();
    cv.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
    const cap = cv.measureText('HÁ').actualBoundingBoxAscent;
    const arriba = (base - cap) - r.top - parseFloat(s.borderTopWidth);
    const abajo = r.bottom - parseFloat(s.borderBottomWidth) - base;
    if (Math.abs(arriba - abajo) > Math.max(3, fs*0.18))
      out.push({tipo:'RELLENO DESIGUAL', detalle:`${name(el)}: ${arriba.toFixed(0)}px arriba de la letra y ${abajo.toFixed(0)}px abajo; centrar sobre el cuerpo visible`});
  }
  // 9. SVG: puntos (círculos chicos) montados sobre el contorno de una elipse o círculo grande
  const pz = el => { const r = el.getBoundingClientRect(); return {x:(r.left+r.right)/2, y:(r.top+r.bottom)/2, rx:r.width/2, ry:r.height/2}; };
  const svgs = [...document.querySelectorAll('svg')];
  for (const sv of svgs) {
    if (sv.closest('.katex')) continue;
    const formas = [...sv.querySelectorAll('circle, ellipse')].filter(vis).map(e => ({e, ...pz(e)}));
    const grandes = formas.filter(f => f.rx > 30 && f.ry > 20), chicos = formas.filter(f => f.rx <= 8);
    for (const p of chicos) for (const g of grandes) {
      const d = Math.hypot((p.x-g.x)/g.rx, (p.y-g.y)/g.ry), tol = (p.rx+2)/Math.min(g.rx, g.ry);
      if (Math.abs(d-1) < tol) { out.push({tipo:'PUNTO SOBRE EL BORDE', detalle:`punto en (${p.x.toFixed(0)}, ${p.y.toFixed(0)}) toca el contorno de <${g.e.tagName}>; debe quedar claramente dentro o fuera`}); break; }
    }
  }
  // 10. SVG: curvas (no subrayados) que rozan una etiqueta
  for (const g of document.querySelectorAll('svg path, svg polyline')) {
    if (!vis(g) || !g.getTotalLength || g.closest('.katex') || g.closest('.relleno')) continue;
    const bb = g.getBoundingClientRect(); if (bb.height < 10 || bb.width < 10) continue;
    let Lg; try { Lg = g.getTotalLength(); } catch(e) { continue; }
    const m = g.getScreenCTM(); if (!m || !Lg) continue;
    const toca = new Set();
    for (let d=0, paso=Math.max(2, Lg/1500); d<=Lg; d+=paso) {
      const pt = g.getPointAtLength(d), x = pt.x*m.a+pt.y*m.c+m.e, y = pt.x*m.b+pt.y*m.d+m.f;
      for (const it of items) { if (!it.el.closest('svg')) continue; const b = it.b, h = 2;
        if (x>b.left-h && x<b.right+h && y>b.top+b.height*0.25-h && y<b.bottom+h) toca.add(it.el); }
    }
    for (const el of toca) out.push({tipo:'CURVA ROZA ETIQUETA', detalle:`${name(el)} queda sobre o pegada a una curva; moverla fuera del trazo`});
  }
  // 11. Fórmulas: errores de KaTeX, TeX sin renderizar, exponentes/subíndices diminutos
  for (const e of document.querySelectorAll('.katex-error'))
    out.push({tipo:'FÓRMULA CON ERROR', detalle:`"${(e.getAttribute('title')||e.textContent).slice(0,90)}"`});
  const crudo = /(\\(frac|sqrt|bar|hat|alpha|sigma|mu|sum|cdot|le|ge|nu)\b|\$[^$\s][^$]*\$|\\\(|\\\[)/;
  const w2 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let tn;
  while ((tn = w2.nextNode())) { const p = tn.parentElement;
    if (!p || p.closest('script,style,code,pre,.katex,annotation')) continue;
    if (crudo.test(tn.textContent)) out.push({tipo:'FÓRMULA SIN RENDERIZAR', detalle:`"${tn.textContent.trim().slice(0,60)}"`}); }
  for (const k of document.querySelectorAll('.katex .msupsub, .katex .vlist-t2 .sizing')) {
    const fs = parseFloat(getComputedStyle(k).fontSize);
    if (fs && fs < 7.5) { out.push({tipo:'SUBÍNDICE ILEGIBLE', detalle:`${name(k.closest('.katex'))}: índice de ${fs.toFixed(1)}px; subir el tamaño base de la fórmula`}); break; }
  }
  // 12. Subrayado despegado de la palabra (debe ser la base de la letra, no una línea aparte)
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el) || el.closest('svg') || el.closest('.katex')) continue;
    const s = getComputedStyle(el);
    if (!s.textDecorationLine.includes('underline') || s.textUnderlineOffset === 'auto') continue;
    const off = parseFloat(s.textUnderlineOffset), fs = parseFloat(s.fontSize);
    if (off > fs*0.15) out.push({tipo:'SUBRAYADO DESPEGADO', detalle:`${name(el)}: separación de ${off.toFixed(1)}px (máximo ${(fs*0.15).toFixed(1)}px); usar text-underline-offset: 0.08em`});
  }
  // 13. Idioma declarado (sin lang="es" no hay separación silábica correcta)
  if (!(document.documentElement.getAttribute('lang') || '').startsWith('es') && document.body.innerText.length > 400)
    out.push({tipo:'IDIOMA NO DECLARADO', detalle:'poner <html lang="es"> para que la separación silábica y las comillas sean del español'});
  // 14. Signos tipográficos (avisos; se corrigen con geo.tipografia)
  const reglas = [[/\.\.\./, 'tres puntos en vez de …'], [/"/, 'comillas rectas en vez de “ ”'], [/\S - \S/, 'guion entre espacios en vez de raya —'],
                  [/(^|[\s(=])-\d/, 'guion en vez del signo menos −'], [/\d (%|mm|cm|km|kg|pt|años)(?![\w])/, 'número y unidad separables en dos líneas']];
  const vistosT = new Set(); const w3 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let t3;
  while ((t3 = w3.nextNode())) { const p = t3.parentElement;
    if (!p || p.closest('script,style,code,pre,.katex,annotation,svg') || !vis(p)) continue;
    for (const [re, msg] of reglas) if (!vistosT.has(msg) && re.test(t3.textContent)) { vistosT.add(msg);
      out.push({tipo:'TIPOGRAFÍA', nivel:'aviso', detalle:`${msg}: "${t3.textContent.trim().slice(0,40)}" (usar geo.tipografia)`}); } }
  // 15. Colores que codifican significado: ¿se distinguen en blanco y negro y con daltonismo rojo-verde?
  const usos = new Map(); const sum = c => { if (!c || c.a < 0.5) return; const k = `${c.r},${c.g},${c.b}`; usos.set(k, (usos.get(k)||0) + 1); };
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el) || el.closest('.katex')) continue; const s = getComputedStyle(el);
    if ([...el.childNodes].some(x => x.nodeType===3 && x.textContent.trim())) sum(rgb(el.closest('svg') ? s.fill : s.color));
    if (s.textDecorationLine.includes('underline')) sum(rgb(s.textDecorationColor));
    if (parseFloat(s.borderTopWidth) > 0 || parseFloat(s.borderBottomWidth) > 0) sum(rgb(s.borderBottomColor));
    if (el.closest('svg') && !el.closest('.relleno') && !['text','tspan'].includes(el.tagName)) { if (s.stroke !== 'none') sum(rgb(s.stroke)); }
  }
  const lin = x => { x/=255; return x<=0.04045 ? x/12.92 : ((x+0.055)/1.055)**2.4; };
  const lab = ([r,g,b]) => { const R=lin(r),G=lin(g),B=lin(b);
    const X=(0.4124*R+0.3576*G+0.1805*B)/0.9505, Y=0.2126*R+0.7152*G+0.0722*B, Z=(0.0193*R+0.1192*G+0.9505*B)/1.089;
    const f = v => v > 0.008856 ? Math.cbrt(v) : 7.787*v + 16/116; return [116*f(Y)-16, 500*(f(X)-f(Y)), 200*(f(Y)-f(Z))]; };
  const deut = ([r,g,b]) => { const R=lin(r),G=lin(g),B=lin(b), g2 = v => 255*(v<=0.0031308 ? 12.92*v : 1.055*Math.pow(Math.max(v,0),1/2.4)-0.055);
    return [g2(0.367322*R+0.860646*G-0.227968*B), g2(0.280085*R+0.672501*G+0.047413*B), g2(-0.011820*R+0.042940*G+0.968881*B)]; };
  const dE = (a,b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
  const sat = ([r,g,b]) => (Math.max(r,g,b) - Math.min(r,g,b)) / 255;
  const cols = [...usos].filter(([k,n]) => n >= 2 && sat(k.split(',').map(Number)) > 0.3).map(([k]) => k.split(',').map(Number));
  const hex = c => '#' + c.map(v => Math.round(v).toString(16).padStart(2,'0')).join('').toUpperCase();
  for (let i=0;i<cols.length;i++) for (let j=i+1;j<cols.length;j++) {
    const a = cols[i], b = cols[j], la = lab(a), lb = lab(b);
    if (dE(la, lb) < 25) continue;
    if (Math.abs(la[0]-lb[0]) < 10) out.push({tipo:'COLORES IGUALES EN BLANCO Y NEGRO', nivel:'aviso', detalle:`${hex(a)} y ${hex(b)} tienen casi la misma luminosidad: impresos en grises se confunden; reforzar con otro rasgo (sencillo/doble, sólido/punteado) si distinguen categorías`});
    if (dE(lab(deut(a)), lab(deut(b))) < 20) out.push({tipo:'COLORES CONFUNDIBLES CON DALTONISMO', nivel:'aviso', detalle:`${hex(a)} y ${hex(b)} se confunden con daltonismo rojo-verde; reforzar con otro rasgo si distinguen categorías`});
  }
  // 16. Consistencia: elementos del mismo tipo (misma etiqueta y clases) deben verse iguales
  const grupos = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('svg, .katex, script, style, head') || !vis(e)) continue;
    const tag = e.tagName.toLowerCase();
    const cls = [...e.classList].filter(c => !/^(tema-\d+|katex.*|ZQ.*)$/.test(c)).sort().join('.');
    if (!cls && !/^h[1-4]$/.test(tag)) continue;
    const k = tag + (cls ? '.' + cls : '');
    if (!grupos.has(k)) grupos.set(k, []); grupos.get(k).push(e);
  }
  const PROPS = [['fontSize','tamaño de letra'], ['fontWeight','peso'], ['fontFamily','fuente'], ['color','color'],
    ['paddingTop','relleno superior'], ['paddingLeft','relleno lateral'], ['borderTopWidth','grosor de borde'],
    ['borderTopLeftRadius','redondeo'], ['backgroundColor','fondo'], ['textDecorationColor','color de subrayado']];
  for (const [k, els] of grupos) {
    if (els.length < 3) continue;
    for (const [p, nom] of PROPS) {
      const cuenta = new Map();
      for (const e of els) { const v = getComputedStyle(e)[p]; cuenta.set(v, (cuenta.get(v) || 0) + 1); }
      if (cuenta.size < 2) continue;
      const [modo, n] = [...cuenta].sort((a, b) => b[1] - a[1])[0];
      if (n / els.length < 0.6) continue;           // sin mayoría clara: variación intencional
      const raros = els.filter(e => getComputedStyle(e)[p] !== modo);
      out.push({tipo:'INCONSISTENCIA', nivel:'aviso', detalle:`${raros.length} de ${els.length} <${k}> tienen otro ${nom} (${getComputedStyle(raros[0])[p]} en vez de ${modo}), p. ej. "${(raros[0].textContent||'').trim().slice(0,30)}"`});
    }
  }
  const seen = new Set();
  return out.filter(o => { const k=o.tipo+o.detalle; if (seen.has(k)) return false; seen.add(k); return true; });
}
"""

CACHE = Path.home() / '.cache' / 'maquetacion-fuentes'
_CDN_OK = {}
FALLAS = []

def fuente_local(familia):
    """Descarga la fuente de npm (@fontsource) y devuelve CSS @font-face local."""
    slug = familia.lower().replace(' ', '-')
    d = CACHE / slug
    if not d.exists():
        d.mkdir(parents=True)
        try:
            subprocess.run(['npm', 'pack', f'@fontsource/{slug}', '--silent'], cwd=d, check=True, capture_output=True)
            tgz = next(d.glob('*.tgz'))
            subprocess.run(['tar', '-xzf', tgz.name], cwd=d, check=True)
        except Exception:
            return ''
    css = []
    for f in sorted((d / 'package' / 'files').glob(f'{slug}-latin*-normal.woff2')):
        partes = f.stem.split('-')
        peso = next((x for x in partes if x.isdigit()), '400')
        if 'ext' in partes:
            continue
        css.append(f"@font-face{{font-family:'{familia}';font-weight:{peso};src:url('{f.as_uri()}') format('woff2')}}")
    return '\n'.join(css)

def ruta_fuentes(route):
    if _CDN_OK.get('gf') is not False:
        try:
            resp = route.fetch(timeout=6000)
            if resp.ok:
                _CDN_OK['gf'] = True
                return route.fulfill(response=resp)
        except Exception:
            pass
        _CDN_OK['gf'] = False
    from urllib.parse import urlparse, parse_qs
    fams = [f.split(':')[0].replace('+', ' ') for f in parse_qs(urlparse(route.request.url).query).get('family', [])]
    css = '\n'.join(fuente_local(f) for f in fams)
    for f in fams:
        if f"'{f}'" not in css:
            FALLAS.append(f)
    route.fulfill(status=200, content_type='text/css', body=css)

KATEX_VER = '0.16.11'

def katex_local():
    d = CACHE / 'katex'
    if not (d / 'package' / 'dist' / 'katex.min.js').exists():
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(['npm', 'pack', f'katex@{KATEX_VER}', '--silent'], cwd=d, check=True, capture_output=True)
        subprocess.run(['tar', '-xzf', next(d.glob('katex-*.tgz')).name], cwd=d, check=True)
    return d / 'package'

def ruta_katex(route):
    """Sirve KaTeX (css, js, fuentes, auto-render) desde npm si el CDN no responde (se prueba una sola vez)."""
    if _CDN_OK.get('katex') is not False:
        try:
            resp = route.fetch(timeout=4000)
            if resp.ok:
                _CDN_OK['katex'] = True
                return route.fulfill(response=resp)
        except Exception:
            pass
        _CDN_OK['katex'] = False
    url = route.request.url.split('?')[0]
    i = url.find('/dist/')
    if i < 0:
        return route.abort()
    f = katex_local() / url[i+1:]
    if not f.exists():
        return route.abort()
    tipos = {'.css': 'text/css', '.js': 'application/javascript', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf'}
    route.fulfill(status=200, body=f.read_bytes(), content_type=tipos.get(f.suffix, 'application/octet-stream'))

# ───────────── Revisión página por página (solo con --pdf) ─────────────

MARCAR = r"""
() => {
  const vis = el => { const s = getComputedStyle(el); return s.display !== 'none' && s.visibility !== 'hidden'; };
  const txt = el => (el.textContent || '').replace(/ZQ\d+[SE]/g, '').trim().replace(/\s+/g, ' ').slice(0, 40);
  let k = 0; const meta = [];
  const span = (id, lado) => { const m = document.createElement('span');
    m.textContent = `ZQ${id}${lado}`;
    m.style.cssText = `position:absolute;${lado==='S'?'top':'bottom'}:0;left:0;font-size:2px;line-height:2px;color:rgba(0,0,0,0.01);white-space:nowrap;pointer-events:none`;
    return m; };
  const anclar = (el, id, ambos) => {
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    el.prepend(span(id, 'S')); if (ambos) el.append(span(id, 'E')); };
  // temas: h1 y todo lo que fuerza página nueva
  const temas = [...document.querySelectorAll('body *')].filter(e => vis(e) && !e.closest('svg,.katex') &&
      (e.tagName === 'H1' || ['page','always','left','right','recto','verso'].includes(getComputedStyle(e).breakBefore)));
  const vistos = new Set();
  for (const e of temas) { if ([...vistos].some(v => v.contains(e))) continue; vistos.add(e);
    const id = ++k; anclar(e, id, false); meta.push({id, tipo:'tema', nombre: txt(e.querySelector('h1,h2') || e)}); }
  for (const e of document.querySelectorAll('h2, h3')) { if (!vis(e) || e.closest('svg,.katex')) continue;
    if ([...vistos].some(v => v === e)) continue;
    const id = ++k; anclar(e, id, false); meta.push({id, tipo:'titulo', nombre: txt(e)}); }
  // bloques que no deben partirse
  const cands = [...document.querySelectorAll('table, figure, pre, blockquote, .formula, .bloque, .katex-display, svg, [class*="caja"], [class*="recuadro"]')]
     .concat([...document.querySelectorAll('body *')].filter(e => getComputedStyle(e).breakInside === 'avoid'))
     .filter(e => vis(e) && !e.closest('.katex') && !(e.tagName !== 'svg' && e.closest('svg')) && !(e.tagName === 'svg' && e.parentElement.closest('svg')));
  const unicos = [...new Set(cands)];
  const externos = unicos.filter(e => !unicos.some(o => o !== e && o.contains(e)));
  for (const e of externos) {
    const id = ++k, r = e.getBoundingClientRect();
    let destino = e;
    if (e.tagName === 'TABLE') {
      const celdas = e.querySelectorAll('th, td'); if (!celdas.length) continue;
      const a = celdas[0], z = celdas[celdas.length-1];
      for (const c of [a, z]) if (getComputedStyle(c).position === 'static') c.style.position = 'relative';
      a.prepend(span(id, 'S')); z.append(span(id, 'E'));
      meta.push({id, tipo:'tabla', nombre: txt(e), thead: !!e.querySelector('thead'), alto: r.height}); continue;
    }
    if (e.tagName === 'svg') {
      const w = document.createElement(getComputedStyle(e).display === 'inline' ? 'span' : 'div');
      w.style.cssText = 'position:relative;display:' + (getComputedStyle(e).display === 'inline' ? 'inline-block' : 'block') + ';margin:0;padding:0';
      e.parentNode.insertBefore(w, e); w.appendChild(e); destino = w;
    }
    anclar(destino, id, true);
    meta.push({id, tipo:'bloque', nombre: txt(e) || '<' + e.tagName.toLowerCase() + '>', alto: r.height});
  }
  // márgenes de @page (para saber el área útil)
  let mb = null, mt = null;
  for (const sh of document.styleSheets) { let rs; try { rs = sh.cssRules; } catch(e) { continue; }
    for (const ru of rs) if (ru.type === 6 || ru.constructor.name === 'CSSPageRule') {
      if (ru.style.marginTop) mt = ru.style.marginTop; if (ru.style.marginBottom) mb = ru.style.marginBottom; } }
  return {meta, mt, mb};
}
"""

def _a_pt(v, defecto_mm=15):
    if not v: return defecto_mm * 72 / 25.4
    v = v.strip()
    try:
        if v.endswith('mm'): return float(v[:-2]) * 72 / 25.4
        if v.endswith('cm'): return float(v[:-2]) * 720 / 25.4
        if v.endswith('in'): return float(v[:-2]) * 72
        if v.endswith('pt'): return float(v[:-2])
        if v.endswith('px'): return float(v[:-2]) * 0.75
    except ValueError:
        pass
    return defecto_mm * 72 / 25.4

def revisar_paginas(pdf_path, info):
    """Analiza el PDF ya paginado: temas en página nueva, bloques partidos, títulos huérfanos,
    líneas colgadas y espacio muerto."""
    try:
        import pdfplumber
    except ImportError:
        return [{'tipo': 'REVISIÓN DE PÁGINAS OMITIDA', 'detalle': 'falta pdfplumber (pip install pdfplumber)'}]
    import re
    meta = {m['id']: m for m in info['meta']}
    out, paginas = [], []
    with pdfplumber.open(pdf_path) as pdf:
        for pa in pdf.pages:
            H = pa.height
            marcas = {}
            chars = sorted([c for c in pa.chars if c['size'] < 2.6], key=lambda c: (c['top'], c['x0']))
            buf, top0 = '', None
            for c in chars + [None]:
                if c is not None and (top0 is None or abs(c['top'] - top0) < 1.5):
                    buf += c['text']; top0 = c['top'] if top0 is None else top0; continue
                for mm in re.finditer(r'ZQ(\d+)([SE])', buf): marcas[(int(mm.group(1)), mm.group(2))] = top0
                buf, top0 = (c['text'], c['top']) if c is not None else ('', None)
            limpia = pa.filter(lambda o: o.get('object_type') != 'char' or o['size'] >= 2.6)
            palabras = limpia.extract_words()
            graf = [(o['top'], o['bottom']) for o in (limpia.rects + limpia.lines + limpia.curves) if o['bottom'] - o['top'] < H * 0.95]
            paginas.append({'H': H, 'marcas': marcas, 'palabras': palabras, 'graf': graf})
    # encabezados y pies repetidos: líneas en el 9 % superior/inferior con el mismo texto (sin números) en ≥ 2 páginas
    def firma(t): return re.sub(r'\d+', '#', t)
    zonas = {}
    for p in paginas:
        lineas = {}
        for w in p['palabras']:
            if w['top'] > p['H'] * 0.91 or w['bottom'] < p['H'] * 0.09:
                lineas.setdefault(round(w['top']), []).append(w['text'])
        for t, ws in lineas.items(): zonas.setdefault(firma(' '.join(ws)), set()).add(t)
    repetidas = {f for f, s in zonas.items() if len(paginas) > 1 and sum(1 for p in paginas for w in p['palabras']
                 if firma(w['text']) and firma(w['text']) in f) >= 2}
    for p in paginas:
        lineas = {}
        for w in p['palabras']: lineas.setdefault(round(w['top']), []).append(w)
        fuera = set()
        for t, ws in lineas.items():
            if (t > p['H'] * 0.91 or t < p['H'] * 0.09) and firma(' '.join(w['text'] for w in ws)) in repetidas:
                fuera |= {id(w) for w in ws}
        p['items'] = [(w['top'], w['bottom']) for w in p['palabras'] if id(w) not in fuera] + p['graf']
    mt, mb = _a_pt(info.get('mt')), _a_pt(info.get('mb'))
    H = paginas[0]['H'] if paginas else 842
    arriba, abajo = mt, H - mb
    util = abajo - arriba
    pag_de = {}
    for n, p in enumerate(paginas, 1):
        for (mid, lado), y in p['marcas'].items(): pag_de[(mid, lado)] = (n, y)
    def items(n, desde=-1e9, hasta=1e9):
        return [it for it in paginas[n-1]['items'] if it[0] >= desde - 0.5 and it[1] <= hasta + 0.5 and it[0] < abajo + 2]
    temas_ini = {pag_de[(m['id'], 'S')][0] for m in meta.values() if m['tipo'] == 'tema' and (m['id'], 'S') in pag_de}
    # 1. Tema nuevo en página limpia
    temas = [m for m in sorted(meta.values(), key=lambda m: m['id']) if m['tipo'] == 'tema']
    for m in temas[1:]:
        if (m['id'], 'S') not in pag_de: continue
        n, y = pag_de[(m['id'], 'S')]
        previos = [it for it in items(n) if it[1] < y - 2]
        if previos:
            out.append({'tipo': 'TEMA NO EMPIEZA EN PÁGINA NUEVA', 'detalle': f'"{m["nombre"]}" (página {n}): poner break-before: page en su contenedor'})
    # 2. Bloques partidos
    for m in meta.values():
        if m['tipo'] not in ('bloque', 'tabla') or (m['id'], 'S') not in pag_de or (m['id'], 'E') not in pag_de: continue
        n1, n2 = pag_de[(m['id'], 'S')][0], pag_de[(m['id'], 'E')][0]
        if n1 == n2: continue
        alto_pt = m.get('alto', 0) * 0.75
        if m['tipo'] == 'tabla':
            if alto_pt > util * 0.6:
                if not m.get('thead'):
                    out.append({'tipo': 'TABLA PARTIDA SIN ENCABEZADO', 'detalle': f'"{m["nombre"]}" (páginas {n1}–{n2}): poner la fila de títulos en <thead> para que se repita'})
                continue
        if alto_pt > util:
            out.append({'tipo': 'BLOQUE MÁS ALTO QUE UNA PÁGINA', 'detalle': f'"{m["nombre"]}" (páginas {n1}–{n2}): dividirlo en partes con sentido propio'})
        else:
            out.append({'tipo': 'BLOQUE PARTIDO ENTRE PÁGINAS', 'detalle': f'"{m["nombre"]}" (páginas {n1}–{n2}): break-inside: avoid o reacomodar'})
    # 3. Títulos huérfanos al pie
    for m in meta.values():
        if m['tipo'] not in ('titulo', 'tema') or (m['id'], 'S') not in pag_de: continue
        n, y = pag_de[(m['id'], 'S')]
        if n >= len(paginas): continue
        despues = [it for it in items(n, desde=y)]
        fondo = max((it[1] for it in despues), default=y)
        if y > arriba + util * 0.7 and fondo - y < util * 0.09:
            out.append({'tipo': 'TÍTULO HUÉRFANO AL PIE', 'detalle': f'"{m["nombre"]}" queda al final de la página {n} y su contenido sigue en la {n+1}: break-after: avoid o reacomodar'})
    # 4. Líneas colgadas al inicio de una página
    for n in range(2, len(paginas) + 1):
        if n in temas_ini: continue
        tops = [y for (mid, lado), (pn, y) in pag_de.items() if pn == n and lado == 'S' and meta.get(mid, {}).get('tipo') in ('titulo', 'tema')]
        corte = min(tops) if tops else 1e9
        frag = [it for it in items(n) if it[1] <= corte - 1]
        if not frag: continue
        ext = max(it[1] for it in frag) - min(it[0] for it in frag)
        resto = [it for it in items(n) if it[0] >= corte - 1]
        if ext < util * 0.12 and (resto or len(items(n)) == len(frag)):
            nl = len({round(it[0] / 3) for it in frag})
            out.append({'tipo': 'LÍNEAS COLGADAS', 'detalle': f'página {n} empieza con un fragmento suelto (~{min(nl, 9)} líneas) del subtema anterior: condensar la redacción para que cierre en la página {n-1}'})
    # 5. Espacio muerto a mitad de un tema
    for n in range(1, len(paginas)):
        if (n + 1) in temas_ini: continue
        its = items(n)
        fondo = max((it[1] for it in its), default=arriba)
        vacio = (abajo - fondo) / util
        if vacio > 0.25:
            out.append({'tipo': 'ESPACIO MUERTO', 'detalle': f'página {n}: {vacio*100:.0f} % vacío a mitad de tema (un bloque grande se fue a la página {n+1}); reacomodar o dividir el bloque'})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('archivo'); ap.add_argument('--ancho', type=int, default=900)
    ap.add_argument('--alto', type=int, default=0); ap.add_argument('--pdf', action='store_true')
    ap.add_argument('--salida', default=None)
    a = ap.parse_args()
    src = Path(a.archivo).resolve()
    out = Path(a.salida or src.parent / (src.stem + '_revision')); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': a.ancho, 'height': a.alto or 200}, device_scale_factor=2)
        pg.route('**/fonts.googleapis.com/**', ruta_fuentes)
        pg.route('**/katex*/dist/**', ruta_katex)
        pg.goto(src.as_uri()); pg.wait_for_load_state('networkidle')
        malas = pg.evaluate("async()=>{await document.fonts.ready; return [...document.fonts].filter(f=>f.status==='error').map(f=>f.family)}")
        pg.wait_for_timeout(300)
        if not a.alto:  # todo el contenido dentro de la ventana, para que la detección por punto funcione
            alto_total = pg.evaluate("document.documentElement.scrollHeight")
            pg.set_viewport_size({'width': a.ancho, 'height': min(alto_total, 16000)}); pg.wait_for_timeout(150)
        problemas = pg.evaluate(JS)
        for f in sorted(set(FALLAS + malas)):
            problemas.insert(0, {'tipo': 'FUENTE NO CARGÓ', 'detalle': f'{f}: las medidas no son confiables; resolver antes de seguir'})
        png = out / 'vista.png'; pg.screenshot(path=str(png), full_page=not a.alto)
        pngs = [str(png)]
        if a.pdf:
            pdf = out / 'vista.pdf'
            info = pg.evaluate(MARCAR)
            pg.emulate_media(media='print')
            pg.pdf(path=str(pdf), format='A4', print_background=True, prefer_css_page_size=True)
            try:
                subprocess.run(['pdftoppm', '-r', '150', '-png', str(pdf), str(out / 'pagina')], check=True)
                pngs = sorted(str(x) for x in out.glob('pagina*.png'))
            except Exception as e:
                print('Aviso: no se pudo rasterizar el PDF:', e)
            problemas += revisar_paginas(str(pdf), info)
        b.close()
    avisos = [x for x in problemas if x.get('nivel') == 'aviso']
    problemas = [x for x in problemas if x.get('nivel') != 'aviso']
    try:
        from PIL import Image
        bn = out / 'vista_bn.png'; Image.open(png).convert('L').save(bn); pngs.append(str(bn))
    except Exception:
        pass
    print(json.dumps({'problemas': len(problemas), 'detalle': problemas, 'avisos': avisos, 'imagenes': pngs}, ensure_ascii=False, indent=1))
    sys.exit(1 if problemas else 0)

if __name__ == '__main__':
    main()
