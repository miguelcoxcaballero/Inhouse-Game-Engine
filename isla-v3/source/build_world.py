"""Assemble the 100 km² island around the audited rigid-block city mesh."""
import json,gzip,pathlib,sys,math,warnings
warnings.filterwarnings('ignore',category=DeprecationWarning)
import numpy as np
from shapely.geometry import shape,mapping,Point,Polygon,LineString,box
from shapely.ops import unary_union,transform,nearest_points
from shapely.affinity import translate
from shapely import make_valid,contains_xy,STRtree
from scipy.interpolate import RBFInterpolator
from scipy.ndimage import gaussian_filter
from PIL import Image
from matplotlib.colors import LightSource,LinearSegmentedColormap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mesh_city import D,ROOT,OLD,Mesh,rel,osm,fc,feature,parts

B=json.load(gzip.open(D/'baseline-49.json.gz'));fs=json.load(open(D/'city-features.geojson'))['features'];landmarks=json.load(open(D/'city-landmarks.json'));review=json.load(open(D/'city-mesh-review.json'))
npz=np.load(D/'displacement-mesh.npz');mesh=Mesh(npz['source'],npz['destination'])
def add(g,k,**p):
 if not g.is_empty:fs.append(feature(make_valid(g),k,**p))

# The city shore comes from OSM. Only the unpopulated western outline varies to
# meet the exact area budget; buildings, city blocks and the airport never scale.
source_land=rel(json.load(gzip.open(D/'source-coast.geojson.gz')))
city_land=mesh.geometry(source_land.intersection(box(-4900,-5600,5700,8000)))
# Replace the rectangular northern extraction edge with an island shore. The
# released farmland area goes to the western mountains, keeping the budget fixed.
from scipy.interpolate import PchipInterpolator
nx=np.array([-10000,-3400,-2100,-800,600,2200,3300,4500,5000,5400,10000])
ny=np.array([3900,4400,5550,5000,3800,3700,4200,5200,5100,4950,4900])
xx=np.linspace(-10000,10000,401);yy=PchipInterpolator(nx,ny)(xx)
northern_mask=Polygon([(-10000,-10000),(10000,-10000),*zip(xx[::-1],yy[::-1])])
city_land=city_land.intersection(northern_mask)
west=[(-6300,1500),(-5900,3500),(-4500,5000),(-2500,5700),(-1300,5200),(-1300,-2000),(-3000,-3100),(-4900,-2500),(-5800,-800)]
south=Polygon([(-4400,-2200),(-1200,-1800),(3000,-2000),(3200,-3400),(2700,-4700),(2300,-5700),(1100,-6300),(0,-6000),(-1000,-6500),(-2400,-5300),(-3500,-3800)])
airport_reserve=translate(shape(B['airport-layout.json']['footprint']),-2800,350).buffer(90)
bonaire_reserve=unary_union([translate(shape(f['geometry']),-2200,-300) for f in B['isla-metros.geojson']['features'] if 'Bonaire' in f['properties'].get('name','') and f['properties']['kind'] in ['industrial','landmark-footprint']]).convex_hull.buffer(200)
def outline(extra):
 w=Polygon([(x-extra*max(0,min(1,(-x-1300)/3500)),y) for x,y in west])
 merged=make_valid(unary_union([city_land,w,south,airport_reserve,bonaire_reserve]).buffer(55).buffer(-55))
 main=max(parts(merged,'Polygon'),key=lambda p:p.area)
 return Polygon(main.exterior) # budget includes interior waters, as in V02
lo,hi=-2000.,5000.
for _ in range(65):
 mid=(lo+hi)/2
 if outline(mid).area<100e6:lo=mid
 else:hi=mid
coast=outline((lo+hi)/2)
assert abs(coast.area/1e6-100)<1e-7,coast.area
assert coast.geom_type=='Polygon','Island must be one connected polygon'
print('ISLAND',coast.area/1e6,coast.bounds,'west adjustment',(lo+hi)/2,flush=True)

# Only clipping of imported regional roads/land use is allowed at the new coast.
# Complete urban footprints must fit; otherwise enlarge/recompose the coast.
for f in fs:
 g=shape(f['geometry']);p=f['properties']
 if p['kind'] in ['building','protected-landmark','landmark-footprint']:
  if not coast.buffer(.01).covers(g):raise RuntimeError('City footprint outside island: '+str((p.get('kind'),p.get('osm',p.get('name','')),g.difference(coast).area,g.bounds)))
 elif p['kind']=='city-block':pass # source selection masks can include marina water
 else:f['geometry']=mapping(g.intersection(coast))
fs=[f for f in fs if not shape(f['geometry']).is_empty]

# Regional anchors move whole town sectors. Roads between them use a smooth
# field; the destination town street network keeps its original metric geometry.
deltas={'airport':(-2800,350),'chelva':(-2700,1100),'benageber':(-2800,700),'cofrentes':(-1600,-500),'jalance':(-1600,-500),'south':(-300,-900),'albufera':(250,-1400),'bonaire':(-2200,-300)}
def region(p,g):
 c=g.centroid;x,y=c.x,c.y;s=p.get('sector','');n=p.get('name','').lower()
 if p.get('airport') or p.get('kind') in ['airway','airfield'] or 'aerop' in n or 'pista 12/30' in n:return 'airport'
 if s in ['chelva'] or p.get('zone')=='chelva' or ('chelva' in n or 'cortada' in n or 'playeta' in n or 'remedio' in n):return 'chelva'
 if p.get('kind')=='reservoir' or 'benagéber' in n:return 'benageber'
 if 'bonaire' in n:return 'bonaire'
 if s=='jalance':return 'jalance'
 if s in ['cofrentes'] or p.get('zone')=='cofrentes' or x<-1700 and y<200:return 'cofrentes'
 if y<-3750 or p.get('zone')=='sur':return 'south'
 if y<-1000 and x>-1400:return 'albufera'
 if x<0 and y>1900:return 'chelva'
 return None
anchors=[((-2200,800),'airport'),((-1100,1100),'airport'),((-1000,2800),'chelva'),((-1400,2100),'benageber'),((-2450,-700),'cofrentes'),((-2400,-1710),'cofrentes'),((-2180,-2630),'jalance'),((850,-4320),'south'),((2100,-4470),'south'),((1050,-2400),'albufera'),((1850,-1750),'albufera'),((1400,-3270),'albufera'),((-2450,100),'bonaire')]
src=np.array([a for a,k in anchors],float);dst=np.array([np.array(a)+deltas[k] for a,k in anchors])
for x,y in [(600,1000),(1300,1300),(2400,800),(2000,2200),(500,2300)]:
 src=np.vstack([src,[x,y]]);dst=np.vstack([dst,mesh.points([[(x-1100)/.4,(y-1100)/.4]])[0]])
field=RBFInterpolator(src,dst,smoothing=3000)
def warp(x,y,z=None):
 x,y=np.broadcast_arrays(np.asarray(x),np.asarray(y));q=field(np.c_[x.ravel(),y.ravel()]);return q[:,0].reshape(x.shape),q[:,1].reshape(y.shape)
def outside(g):return transform(warp,g)
city_area=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='city-block']).convex_hull.buffer(100)
skip={'coast','city-block','protected-landmark','landmark-footprint','urban-arterial','urban-area','contour','forest','flood-bank','flood-bed','river-water','designed-park','metro','regional','station','transfer','block-edge','promenade','promenade-surface','beach'}
regional=[];airport=None
for f in B['isla-metros.geojson']['features']:
 p=f['properties'];g=shape(f['geometry']);k=p['kind'];r=region(p,g)
 if p.get('city') or k in skip or p.get('sector') in ['saplaya','alboraia','mercavalencia','huerta-sur']:continue
 if r is None and k not in ['expressway','secondary-road','new-road','trail']:continue
 if k=='building' and p.get('zone')=='valencia' and not p.get('airport') and p.get('sector') not in ['sedavi']:continue
 if k in ['retained-road','building','airway','airfield','water','lake','reservoir','industrial','agriculture','patch','rock','green','wetland','circuit'] and r:
  ng=translate(g,*deltas[r])
 else:ng=outside(g)
 if k in ['expressway','secondary-road','new-road']:
  if p.get('ref') in ['V-30','V-21']:continue
  ng=ng.difference(city_area.buffer(-80))
 if k=='building':
  if not coast.covers(ng):continue
  # Do not duplicate peripheral buildings already selected from the city source.
  if ng.intersects(city_area):continue
 else:ng=ng.intersection(coast)
 if ng.is_empty:continue
 props={a:b for a,b in p.items() if a!='kind'};props['region_translation']=r or 'regional road field'
 add(ng,k,**props);regional.append(fs[-1])
 if k=='airfield':airport=ng

# Preserve all 100 requested architectural entries, including El Palmar barracas.
for l in B['landmarks.json']:
 if any(x['id']==l['id'] for x in landmarks):continue
 r=region(l,Point(l['xy']))
 if r:
  q=np.array(l['xy'])+deltas[r];row={**l,'xy':q.tolist()};landmarks.append(row)
  for f in B['isla-metros.geojson']['features']:
   if f['properties']['kind']=='landmark-footprint' and f['properties'].get('id')==l['id']:add(translate(shape(f['geometry']),*deltas[r]),'landmark-footprint',**{k:v for k,v in f['properties'].items() if k!='kind'})
for f in B['isla-metros.geojson']['features']:
 if f['properties']['kind']=='protected-landmark' and not f['properties'].get('city',False):add(translate(shape(f['geometry']),*deltas['albufera']),'protected-landmark',**{k:v for k,v in f['properties'].items() if k!='kind'})
add(coast,'coast',name='Isla Levante · 100 km²')

# Beach fronts use actual urban OSM sand plus coastal strips on the southern lobe.
# Keep existing source promenades on their mapped side of the real-derived beach.
for name,north,south_y in [('El Saler / Devesa',-3400,-4700),('Calpe',-5400,-5900)]:
 pts=[]
 for y in np.linspace(north,south_y,60):
  cut=coast.intersection(LineString([(-10000,y),(10000,y)]))
  if not cut.is_empty:pts.append((cut.bounds[2],y))
 shore=LineString(pts);sand=shore.offset_curve(-35).buffer(35,cap_style=2).intersection(coast);prom=shore.offset_curve(-77).intersection(coast)
 add(sand,'beach',name=name,source='Orilla de diseño');add(prom,'promenade',name='Paseo marítimo · '+name)

# Fix exterior connectors only. City junctions have one shared source mesh.
sys.path.insert(0,str(ROOT/'isla-v2/source'))
from street_network import GroundRouter
roads=[shape(f['geometry']) for f in fs if f['properties']['kind'] in ['retained-road','urban-arterial','expressway','secondary-road','new-road']]
urban=unary_union([shape(f['geometry']) for f in fs if f['properties'].get('city') and f['properties']['kind'] in ['retained-road','urban-arterial','expressway']])
obstacles=unary_union([shape(f['geometry']).buffer(2) for f in fs if f['properties']['kind'] in ['building','lake','reservoir','water','flood-bed']]+[shape(f['geometry']).buffer(85) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'])
router=GroundRouter(coast.bounds,obstacles,coast.buffer(-2),12);attachments=[]
# Retain the previously labelled F1 interpretation beside the expanded harbour,
# repairing only clashes with the now correctly placed, full-size buildings.
old_circuit=next(shape(f['geometry']) for f in B['isla-metros.geojson']['features'] if f['properties']['kind']=='circuit')
circuit=translate(old_circuit,1900,700);points=[circuit.interpolate(s) for s in np.arange(0,circuit.length,12)]
valid=[router.index(p) is not None and not obstacles.intersects(p) and coast.covers(p) for p in points]
if any(valid):
 start=valid.index(True);points=points[start:]+points[:start];points.append(points[0]);out=[points[0].coords[0]];i=0;failed=False
 while i<len(points)-1:
  j=i+1
  while j<len(points)-1 and (obstacles.intersects(points[j]) or not coast.covers(points[j])):j+=1
  g=router.route(points[i],points[j])
  if g is None:failed=True;break
  out.extend(list(g.coords)[1:]);i=j
 if not failed:
  circuit=LineString(out);add(circuit,'circuit',name='Antiguo F1 · interpretación en revisión',source='Bucle de diseño previo recompuesto alrededor del puerto; no réplica histórica exacta')
  landmarks.append({'id':'design-f1-100','name':'Antiguo circuito de Fórmula 1 · interpretación','xy':list(circuit.interpolate(.2,normalized=True).coords[0]),'zone':'valencia','retention':'Interpretación conservada y ajustada al puerto. La fidelidad histórica del trazado sigue pendiente.'})
else:failed=True
if failed:
 # Use a closed sequence of actual harbour streets when the old interpretation
 # no longer fits. This is a proposal, not a claim of historical F1 fidelity.
 import networkx as nx
 graph=nx.Graph();portbox=circuit.envelope.buffer(850)
 for f in fs:
  p=f['properties'];g=shape(f['geometry'])
  if p['kind'] not in ['retained-road','urban-arterial'] or p.get('roadclass') in ['footway','path','steps','cycleway','pedestrian'] or not g.intersects(portbox):continue
  for line in parts(g.intersection(portbox),'LineString'):
   ps=[tuple(np.round(v,3)) for v in line.coords]
   for a,b in zip(ps,ps[1:]):
    if a!=b:graph.add_edge(a,b)
 choices=[]
 for cycle in nx.cycle_basis(graph):
  if len(cycle)<4:continue
  ring=LineString(cycle+[cycle[0]])
  if 1800<ring.length<6500 and ring.is_ring and not ring.intersects(obstacles) and coast.covers(ring):
   area=Polygon(ring).area
   if area>100000:choices.append((abs(ring.length-3600)+ring.centroid.distance(circuit.centroid)*3,ring))
 if not choices:raise RuntimeError('No connected harbour loop available')
 circuit=min(choices,key=lambda v:v[0])[1];add(circuit,'circuit',name='Antiguo F1 · propuesta sobre calles del puerto',source='Bucle cerrado sobre geometría viaria OSM; trazado histórico pendiente de reconstrucción')
 landmarks.append({'id':'design-f1-100','name':'Antiguo circuito de Fórmula 1 · propuesta', 'xy':list(circuit.interpolate(.2,normalized=True).coords[0]),'zone':'valencia','retention':'Bucle cerrado sobre calles del puerto. Propuesta de diseño; no réplica del trazado histórico.'})
# Exterior joins and path checks run in integrate_routes.py.
for name,ll in [('Alboraia · núcleo y mercado',(-.3500,39.501)),('Port Saplaya · marina',(-.3205,39.5105)),('UV · campus Blasco Ibáñez',(-.3608,39.4795)),('UPV · campus de Vera',(-.3435,39.4814)),('Mercavalència · mercado y logística',(-.3509,39.4344))]:
 if not any(l['name']==name for l in landmarks):landmarks.append({'id':'place-'+str(len(landmarks)),'name':name,'xy':mesh.points([rel(mapping(Point(ll))).coords[0]])[0].tolist(),'zone':'valencia','retention':'Referencia OSM guiada por la malla urbana.'})
for kind,name in [('designed-park','Jardín del Turia · antiguo cauce, parque seco'),('flood-bed','Nuevo cauce del Turia · rambla sur')]:
 g=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']==kind]);landmarks.append({'id':'river-'+kind,'name':name,'xy':list(g.representative_point().coords[0]),'zone':'valencia','retention':'Antiguo cauce ajardinado y seco. Nuevo cauce meridional representado por separado; anchuras de diseño.'})

# Stations follow source coordinates where available, otherwise the corresponding
# town translation. Services are a fictional compact network, as requested.
transit=B['transit.json'];station_ll={'mislata':(-.4164,39.4755),'cid':(-.4071,39.4698),'guimera':(-.3854,39.469),'xativa':(-.377,39.4667),'colon':(-.3708,39.4704),'alameda':(-.3654,39.4749),'amistat':(-.3487,39.4709),'maritim':(-.3345,39.4668),'neptu':(-.3237,39.4621),'facultats':(-.3619,39.4789),'benimaclet':(-.3625,39.4857),'alboraia':(-.350,39.501),'empalme':(-.4057,39.5),'turia':(-.3904,39.4797),'patraix':(-.3919,39.4595),'upv':(-.3435,39.4814),'tarongers':(-.3449,39.4768),'cabanyal':(-.3288,39.471),'alacant':(-.3775,39.461),'russafa':(-.3715,39.4613),'arts':(-.3524,39.4557),'natzaret':(-.3327,39.4474)}
station_regions={'airport':'airport','manises':'airport','bonaire':'bonaire','cofrentes':'cofrentes','jalance':'jalance','saler':'albufera','safor':'south','calpe':'south'}
for s in transit['stations']:
 if s['id'] in station_ll:s['xy']=mesh.points([rel(mapping(Point(station_ll[s['id']]))).coords[0]])[0].tolist()
 else:s['xy']=(np.array(s['xy'])+deltas[station_regions.get(s['id'],'albufera')]).tolist()
 add(Point(s['xy']),'station',name=s['name'],id=s['id'])
st={s['id']:s for s in transit['stations']};transit['edges']=[]
for l in transit['lines']:
 points=[st[i]['xy'] for i in l['stations']];g=LineString(points);l['length_m']=round(g.length);add(g,'regional' if l['mode']=='regional' else 'metro',name=l['id'],color=l['color'],source='Esquema de servicios del juego; no túneles ni horarios reales')
 for a,b in zip(l['stations'],l['stations'][1:]):transit['edges'].append({'a':a,'b':b,'line':l['id'],'length_m':Point(st[a]['xy']).distance(Point(st[b]['xy']))})

# Synthetic relief is flat under the urban fabric, parks, airport and floodway.
E=[coast.bounds[0]-100,coast.bounds[1]-100,coast.bounds[2]+100,coast.bounds[3]+100];N=1025;X,Y=np.meshgrid(np.linspace(E[0],E[2],N),np.linspace(E[3],E[1],N));H=np.zeros_like(X)+14
for x,y,h,sx,sy in [(-5100,3600,650,1100,1000),(-5300,-1800,550,950,1200),(-1800,-5100,620,1000,650),(1900,-5400,320,300,400)]:H+=h*np.exp(-(((X-x)/sx)**2+((Y-y)/sy)**2)/2)
rng=np.random.default_rng(100);noise=gaussian_filter(rng.normal(size=H.shape),9);noise/=noise.std();H*=1+.07*noise
flat=city_area.buffer(250)
if airport is not None:flat=flat.union(airport.buffer(130))
flat=flat.union(unary_union([shape(f['geometry']) for f in fs if f['properties']['kind'] in ['flood-bank','designed-park']]))
mask=contains_xy(flat,X,Y);blend=gaussian_filter(mask.astype(float),8);H=H*(1-blend)+14*blend;H[mask]=14
land=contains_xy(coast,X,Y);H[~land]=0
for f in fs:
 if f['properties']['kind'] in ['lake','reservoir','water']:H[contains_xy(shape(f['geometry']),X,Y)]=155 if f['properties']['kind']=='reservoir' else 0
Image.fromarray(np.rint(H*10).astype('uint16')).save(D/'altura-decimetros.png');np.save(D/'height.npy',H.astype('float32'))
cmap=LinearSegmentedColormap.from_list('levante',['#7c9b71','#718c59','#969569','#c1b18a','#dfd2b4']);rgb=LightSource(315,45).shade(H,cmap,vert_exag=1.3,dx=(E[2]-E[0])/N,dy=(E[3]-E[1])/N);rgb[:,:,3]=land;Image.fromarray((rgb*255).astype('uint8')).save(D/'relieve.png')
fig,ax=plt.subplots();cs=ax.contour(X,Y,H,levels=[60,100,150,200,300,400,500,600])
for h,segments in zip(cs.levels,cs.allsegs):
 for points in segments:
  if len(points)>3:add(LineString(points).simplify(7).intersection(coast),'contour',height=int(h))
plt.close(fig)
allbuild=[f for f in fs if f['properties']['kind']=='building'];citybuild=[f for f in allbuild if f['properties'].get('city')];blocks=[f for f in fs if f['properties']['kind']=='city-block'];bridges=[f for f in fs if f['properties']['kind']=='bridge']
metrics={'source_blocks':review['source_blocks'],'city_buildings_before':review['all_source_building_mesh_nodes'],'airport_runway_m':next(shape(f['geometry']).length for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway'),'f1_design_m':circuit.length,'island_area_km2':coast.area/1e6,'surface_budget_km2':{'Isla completa, incluidas aguas interiores':coast.area/1e6},'retained_blocks':review['ordinary_blocks'],'retained_ensembles':len(blocks),'removed_blocks':review['removed_complete_blocks'],'city_buildings_final':len(citybuild),'city_buildings_after':len(citybuild),'city_buildings_selected':len(citybuild),'total_buildings':len(allbuild),'valencia_urban_envelope_km2':city_area.area/1e6,'valencia_urban_footprint_km2':unary_union([shape(f['geometry']) for f in citybuild]).area/1e6,'mesh':review,'bridge_features':len(bridges),'road_main_component_fraction':None,'notes':['100 km² includes inland waters.','Valencia mesh is orientation-checked; exterior road grade separation and navigation remain to be reviewed.','Old Turia bed is a dry urban park. New southern floodway is separate.','Building footprints are 1:1; heights without source measurements are previews.']}
pois=[]
for f in citybuild:
 p=f['properties']
 if p.get('name'):pois.append({'id':p['source_id'],'name':p['name'],'xy':list(shape(f['geometry']).representative_point().coords[0]),'zone':'valencia','category':'Vida cotidiana','osm':p['osm'],'retention':'Edificio OSM íntegro en manzana conservada.'})
for name,obj in [('isla-metros.geojson',{'coordinate_system':'LOCAL_METRES_FICTIONAL',**fc(fs)}),('landmarks.json',landmarks),('metrics.json',metrics),('pois.json',pois),('transit.json',transit),('layout.json',{'island':mapping(coast)}),('terrain.json',{'extent':E,'size':N,'units':'height decimetres; XY metres','source':'Synthetic terrain; not a real DEM'}),('architecture-review.json',B['architecture-review.json'])]:
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
print('WORLD',len(fs),'features',len(allbuild),'buildings',len(bridges),'bridge pieces',flush=True)
