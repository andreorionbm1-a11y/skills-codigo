import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import geo, graficas as G
AZ,VE,RO,TI,GR,AZC="#1E3A8A","#237A3E","#C93636","#1D1D1D","#8A8A8A","#2F6FD6"
F='<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet">'
sub=lambda t:f'<tspan font-size="10" dy="4">{t}</tspan>'
def campana(titulo, sombras, etiquetas, cortes, tipo='normal', df=10, w=460):
    c = G.Curva(40, 170, w-80, 120, tipo, df=df)
    s=[f'<svg width="{w}" height="215" style="display:block">']
    for z1,z2,col in sombras: s.append(f'<path d="{c.area(z1,z2)}" fill="{col}" fill-opacity=".28"/>')
    s.append(f'<path d="{c.eje()}" stroke="{GR}" stroke-width="1.3"/>')
    s.append(f'<path d="{c.trazo()}" fill="none" stroke="{AZ}" stroke-width="2.2" stroke-linejoin="round"/>')
    huecos={}
    for kind,args,lab in etiquetas:
        if kind=='centro':
            x,y=c.etiqueta_area(*args); s.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="15" fill="{TI}" paint-order="stroke" stroke="#fff" stroke-width="0">{lab}</text>')
            huecos[round(x)]=(y-17,y+7)
        else:
            x,y,anc=c.etiqueta_cola(*args); s.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" font-size="14" fill="{TI}">{lab}</text>')
    for z,lab in cortes:
        h=next((v for k,v in huecos.items() if abs(k-c.X(z))<40),None)
        s.append(f'<path d="{c.corte(z,h)}" stroke="{TI}" stroke-width="1.2" stroke-dasharray="4 3" fill="none"/>')
        s.append(f'<text x="{c.X(z):.1f}" y="192" text-anchor="middle" font-size="14" fill="{TI}">{lab}</text>')
    s.append('</svg>'); return f'<h3 style="color:{RO};margin:10px 0 0">{titulo}</h3>'+''.join(s)
b = campana('Área central (normal estándar)', [(-1.96,1.96,AZC),(-9,-1.96,RO),(1.96,9,RO)],
   [('centro',(-1.96,1.96),'1 − α'),('cola',(-1.96,'izq'),'α/2'),('cola',(1.96,'der'),'α/2')],
   [(-1.96,'−z'+sub('α/2')),(0,'0'),(1.96,'z'+sub('α/2'))])
b += campana('Límite inferior: qt(α/2, df)', [(-9,-2.228,RO)], [('cola',(-2.228,'izq'),'α/2')],
   [(-2.228,'−t'+sub('ν, α/2')),(0,'0')], 't', 10)
b += campana('Límite superior: qt(1 − α/2, df)', [(-9,2.228,AZC)], [('centro',(-2.6,2.228),'1 − α/2'),('cola',(2.228,'der'),'α/2')],
   [(0,'0'),(2.228,'t'+sub('ν, α/2'))], 't', 10)
S=(300,150,72,58); s=['<svg width="720" height="290" style="display:block">',
 f'<text x="230" y="22" text-anchor="middle" font-size="16" font-weight="700" fill="{AZ}">POBLACIÓN</text>',
 f'<ellipse cx="230" cy="150" rx="200" ry="105" fill="none" stroke="{AZ}" stroke-width="2"/>',
 f'<ellipse cx="{S[0]}" cy="{S[1]}" rx="{S[2]}" ry="{S[3]}" fill="{VE}" fill-opacity=".08" stroke="{VE}" stroke-width="1.8"/>']
for x,y in G.puntos_en_elipse(230,150,200,105,13,margen=14,sep=24,semilla=4,evitar=[S]): s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{AZ}"/>')
mu=G.puntos_en_elipse(*S,7,margen=13,sep=18,semilla=2)
for x,y in mu: s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{VE}"/>')
s.append(f'<defs><marker id="pv" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{VE}" stroke-width="1.6"/></marker></defs>')
s.append(f'<path d="M446,150 L522,150" stroke="{VE}" stroke-width="2" marker-end="url(#pv)"/><text x="484" y="138" text-anchor="middle" font-size="14" fill="{VE}">seleccionar</text>')
s.append(f'<text x="625" y="68" text-anchor="middle" font-size="16" font-weight="700" fill="{AZ}">MUESTRA</text><ellipse cx="625" cy="150" rx="75" ry="60" fill="none" stroke="{AZ}" stroke-width="2"/>')
for x,y in mu: s.append(f'<circle cx="{x-S[0]+625:.1f}" cy="{y:.1f}" r="5" fill="{VE}"/>')
s.append(f'<text x="230" y="282" text-anchor="middle" font-size="15" fill="{TI}">N  μ  σ²  σ  p</text><text x="625" y="236" text-anchor="middle" font-size="15" fill="{TI}">n  X̄  S²  S  p̂</text></svg>')
b += f'<h3 style="color:{RO};margin:10px 0 0">Población → muestra</h3>'+''.join(s)
open(sys.argv[1],'w').write(f'<html><head>{F}</head><body style="margin:20px;background:#fff;font-family:Kalam">{b}</body></html>')
