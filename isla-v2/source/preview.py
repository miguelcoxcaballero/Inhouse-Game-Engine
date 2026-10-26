import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,PatchCollection
from matplotlib.patches import Polygon as PP
from shapely.geometry import shape
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';fs=json.load(open(D/'isla-metros.geojson'))['features'];metrics=json.load(open(D/'metrics.json'))
fig=plt.figure(figsize=(17,13),facecolor='#0d1922');ax=fig.add_axes([.25,.06,.73,.88]);ax.set_facecolor('#102c38')
terrain=json.load(open(D/'terrain.json'));ext=terrain['extent'];ax.imshow(Image.open(D/'relieve.png'),extent=[ext[0],ext[2],ext[1],ext[3]],zorder=1)
styles={'coast':('#486153',.8,0),'urban-area':('#bdc2b6',.7,3),'forest':('#3e704e',.45,2),'flood-bank':('#899478',1,5),'flood-bed':('#b8b39a',1,5),'green':('#547959',.7,2),'agriculture':('#8d9671',.5,2),'designed-park':('#82a873',.9,5),'water':('#143c49',1,3),'lake':('#1a4856',1,3),'reservoir':('#1a4856',1,4),'river-water':('#367284',1,6),'beach':('#d4bc8d',1,7),'airfield':('#727c77',1,4),'industrial':('#87928a',.9,4),'rock':('#c8b58e',.55,3),'building':('#b9c2b4',.75,7),'landmark-footprint':('#efb7ac',.9,9)}
lines={'urban-arterial':('#f6d5a4',.9,9),'expressway':('#f1c28a',1.1,9),'retained-road':('#b3c2ba',.3,7),'new-road':('#e8b479',.65,8),'secondary-road':('#e8d5ad',.7,8),'promenade':('#fff2d0',1,9),'airway':('#d4dcda',2,9),'bridge':('#fcdfb8',1.1,10),'trail':('#b8ce9a',.7,8),'circuit':('#ff7d9e',1.4,11),'regional':('#fbe48a',1.6,12),'metro':('#89d4e2',1,12),'transfer':('#ffffff',.8,12)}
def polys(g):
 if g.geom_type=='Polygon':yield g
 elif hasattr(g,'geoms'):
  for v in g.geoms:yield from polys(v)
def lns(g):
 if g.geom_type=='LineString':yield list(g.coords)
 elif hasattr(g,'geoms'):
  for v in g.geoms:yield from lns(v)
for kind,(color,alpha,z) in styles.items():
 patches=[]
 for f in fs:
  if f['properties']['kind']==kind:
   for g in polys(shape(f['geometry'])):patches.append(PP(list(g.exterior.coords),closed=True))
 if patches:ax.add_collection(PatchCollection(patches,facecolor=color,edgecolor='none',alpha=alpha,zorder=z))
for kind,(color,width,z) in lines.items():
 seg=[]
 for f in fs:
  if f['properties']['kind']==kind:seg.extend(lns(shape(f['geometry'])))
 if seg:ax.add_collection(LineCollection(seg,colors=color,linewidths=width,zorder=z,linestyles='dashed' if kind=='regional' else 'solid'))
labels=[('CHELVA',(-1000,2800),(-1000,3350)),('Peña Cortada',(-580,3260),(-150,3700)),('Cascadas / Playeta',(-1120,2280),(-350,2450)),('BENAGÉBER',(-1400,2100),(-2800,2150)),('AEROPUERTO',(-2500,1350),(-3670,1730)),('Bonaire',(-2450,100),(-3520,380)),('VALÈNCIA',(1300,700),(1050,1700)),('UPV / UV',(1600,1200),(1250,1900)),('Alboraia / Saplaya',(2100,2650),(1800,3320)),('Playas',(2780,1000),(3300,1350)),('Puerto + antiguo F1',(2510,-500),(3200,-350)),('COFRENTES',(-2450,-700),(-3500,-700)),('CENTRAL',(-2400,-1710),(-3600,-1980)),('ALBUFERA',(1050,-2400),(650,-2350)),('SAFOR',(-450,-4150),(-1450,-4250)),('CALPE',(850,-4320),(600,-4870)),('IFAC',(2090,-4470),(2600,-4750))]
landmarks=json.load(open(D/'landmarks.json'))
anchors={'CHELVA':'Chelva · iglesia','Peña Cortada':'Acueducto de Peña','Cascadas / Playeta':'Cascada de La Playeta','AEROPUERTO':'Pista 12/30','Bonaire':'Bonaire ·','UPV / UV':'UPV · campus','Puerto + antiguo F1':'Puerto de València ·','CENTRAL':'Central nuclear','BENAGÉBER':'Embalse de Benagéber'}
labels=[(name,next((l['xy'] for l in landmarks if anchors.get(name,'\0') in l['name']),pt),text) for name,pt,text in labels]
for name,pt,text in labels:
 ax.annotate(name,pt,xytext=text,color='#f3e7cd',fontsize=10 if name.isupper() else 8.3,fontweight='bold' if name.isupper() else 'normal',ha='center',arrowprops=dict(arrowstyle='-',color='#c1c6b4',lw=.6),bbox=dict(boxstyle='round,pad=.3',facecolor='#142a32',edgecolor='none',alpha=.85),zorder=30)
ax.set_xlim(-4100,3800);ax.set_ylim(-5500,4800);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
for s in ax.spines.values():s.set_visible(False)
fig.text(.04,.91,'INHOUSE / WORLD DESIGN',color='#d9af82',fontsize=10,weight='bold');fig.text(.04,.855,'ISLA\nLEVANTE',color='#f0eadb',fontsize=38,weight='bold',linespacing=.95,va='top')
fig.text(.04,.75,'V02 · BORRADOR EN CURSO',color='#9fc9c5',fontsize=10,weight='bold');fig.text(.04,.68,'49 km²',color='#f0eadb',fontsize=37,weight='bold');fig.text(.04,.645,'Envolvente total, incluidas aguas',color='#adbdbd',fontsize=9)
fig.text(.04,.60,f"{metrics['retained_blocks']} manzanas · escala 1:1\n100 conjuntos protegidos\nAeropuerto OSM · pista de 2,2 km\nPlayas · puerto · antiguo F1\nUniversidades y huerta\nChelva interior + Benagéber\nCentral de Cofrentes\nSafor · Calpe · Ifac",color='#d1dbd1',fontsize=11,linespacing=1.8,va='top')
fig.text(.04,.325,'TRANSPORTE',color='#d9af82',fontsize=10,weight='bold');fig.text(.04,.285,'━  Metro / tranvía compactado\n┄  Cercanías ficticio de la isla',color='#a9d5dc',fontsize=10,linespacing=1.8,va='top')
fig.text(.04,.19,'Aún por revisar:\nuniones de calles, giros y puentes;\nfidelidad del antiguo circuito;\nvalidación del diseño urbano.',color='#b8c1bd',fontsize=10,linespacing=1.6,va='top')
fig.text(.04,.08,'Geometrías OSM + recomposición de diseño.\nRelieve sintético. No es cartografía real.\n© OpenStreetMap contributors · ODbL',color='#819a9f',fontsize=8,linespacing=1.6,va='top')
ax.plot([-3300,-2300],[-4800,-4800],color='#e8debd',lw=2,zorder=40);ax.text(-2800,-4950,'1 km',ha='center',color='#e8debd',fontsize=9)
fig.savefig(P/'previews/progreso-v2.png',dpi=140,facecolor=fig.get_facecolor());print(P/'previews/progreso-v2.png')
