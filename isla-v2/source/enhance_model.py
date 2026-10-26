"""Continuous OSM corridors, new Turia floodway, cartographic detail and real POIs."""
import json,pathlib,math,collections
import numpy as np
from shapely.geometry import shape,mapping,Point,LineString,Polygon,box
from shapely.ops import unary_union,nearest_points,transform
from shapely.affinity import translate,affine_transform
from shapely import make_valid,contains_xy,STRtree
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,LinearSegmentedColormap
from pyproj import Transformer
from corridor_paths import get_path,compact
from compaction import warp
from network_review import components
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';base=json.load(open(D/'isla-base.geojson'));fs=base['features'];landmarks=json.load(open(D/'landmarks-base.json'));coast=shape(json.load(open(D/'layout.json'))['island']);metrics=json.load(open(D/'metrics-base.json'));tr=Transformer.from_crs(4326,25830,always_xy=True).transform;origin=tr(-.377,39.4735)
# OSM way1459912024 is the original intermittent new-cauce water strip.
# Its compact city copy is superseded by the explicit V-30 / Plan Sur corridor.
# Legacy base caches lack IDs on water; the narrow source-derived footprint identifies it.
fs=[f for f in fs if not(f['properties']['kind']=='water' and (f['properties'].get('id')=='w1459912024' or (shape(f['geometry']).area>50000 and shape(f['geometry']).bounds[2]<-400 and shape(f['geometry']).bounds[1]<-500 and shape(f['geometry']).bounds[3]<400)))]
# Replace the cropped expressways, rather than overlaying a second incompatible network.
fs=[f for f in fs if f['properties']['kind']!='expressway' and not(f['properties']['kind']=='new-road' and f['properties'].get('name') in ['València – Chelva','Acceso oeste / aeropuerto'])]
def add(g,k,**p):
 if g.is_empty:return
 g=make_valid(g)
 fs.append({'type':'Feature','geometry':mapping(g),'properties':{'kind':k,'revision':'continuous-corridors',**p}})
def record(name,g,z='valencia',note='Propuesta de diseño; geometría local ficticia.'):
 c=g.representative_point();landmarks.append({'id':'design-'+name,'name':name,'zone':z,'xy':[c.x,c.y],'retention':note,'area_before_m2':0,'area_after_m2':g.area})
configs=[('A-7',(-.507,39.43),(-.478,39.56),[-2800,-100],[-2300,2350]),('V-30',(-.451,39.509),(-.330,39.439),[-2600,-100],[2300,-1600]),('V-21',(-.346,39.495),(-.292,39.56),[1986,1438],[1810,3070]),('A-3',(-.498,39.476),(-.457,39.478),[-2800,-100],[0,650]),('CV-35',(-.431,39.509),(-.995,39.746),[-458.2313409,1511.6233164],[-1050,2670])]
routes={};corridorlog=[];comparisons=[]
for ref,a,b,A,B in configs:
 original,ids,error=get_path(ref,a,b);g,m=compact(original,A,B)
 if ref=='V-30':
  def closer_city(x,y):
   x=np.asarray(x);u=np.clip((x+1700)/1300,0,1);v=np.clip((2300-x)/900,0,1);return x,np.asarray(y)+450*(u*u*(3-2*u))*(v*v*(3-2*v))
  g=transform(closer_city,g);m.update({'design_m':g.length,'method':'OSM corridor with shared northward valley adjustment, up to450m centrally; west approach and port outlet remain fixed.'})
 if ref=='A-3':
  g=affine_transform(original.simplify(12),json.load(open(D/'airport-layout.json'))['matrix']);m.update({'design_m':g.length,'method':'Same longitudinal airport compaction; preserve geographic relationship A-3 / V-11 / runway, rather than independently fitting this road.'})
 routes[ref]=g;corridorlog.append({'ref':ref,'osm_ids':ids,'source_endpoint_selection_error_m':error,**m})
 # Comparison shows the exact polyline used, not a sample of disconnected OSM ways.
 for stage,geom in [('source',translate(original,-origin[0],-origin[1])),('compact',g)]:comparisons.append({'type':'Feature','geometry':mapping(geom),'properties':{'ref':ref,'stage':stage}})
 if ref!='V-30':
  for side in [-6,6]:add(g.offset_curve(side).intersection(coast),'expressway',name=ref,ref=ref,source='OSM · corredor continuo; rectas contraídas más que curvas',osm_ids=','.join(ids))
 for endpoint in [Point(g.coords[0]),Point(g.coords[-1])]:
  if ref!='V-30':
   for side in [-6,6]:
    end=nearest_points(g.offset_curve(side),endpoint)[0];add(LineString([end,endpoint]),'new-road',name='Empalme de diseño · '+ref,source='Conexión conceptual entre calzada y enlace; carriles pendientes')
 record(ref+' · corredor compacto',g,note='Secuencia continua de '+str(len(ids))+' vías OSM. Se acortan las rectas manteniendo los giros de los vértices conservados. La colocación y escala del corredor son de diseño.')
# A recognisable broad diverted floodway south of the compact urban footprint.
cauce=routes['V-30'];c=list(cauce.coords);v=np.array(c[-1])-c[-2];v/=np.linalg.norm(v);end=np.array(c[-1])+v*900;mouth=LineString([c[-1],end]).intersection(coast);cauce=LineString(c+list(mouth.coords)[1:])
bed=cauce.buffer(46,cap_style=2).intersection(coast);embankment=cauce.buffer(66,cap_style=2).intersection(coast)
# Shift open water slightly south to preserve the separation floodway / lagoon.
for f in fs:
 if f['properties']['kind']=='lake':f['geometry']=mapping(translate(shape(f['geometry']),0,-150))
for l in landmarks:
 if l['id']=='r2786392':l['xy'][1]-=150
add(embankment,'flood-bank',name='Nuevo cauce del Turia · taludes de diseño')
add(bed,'flood-bed',name='Nuevo cauce del Turia · lecho de diseño',source='Corredor ficticio inspirado en el Plan Sur; no modelo hidráulico')
svals=np.linspace(0,cauce.length,max(60,int(cauce.length/20)));flow=[]
for s in svals:
 p=cauce.interpolate(s);a=cauce.interpolate(max(0,s-3));b=cauce.interpolate(min(cauce.length,s+3));v=np.array([b.x-a.x,b.y-a.y]);v/=max(np.linalg.norm(v),1);n=np.array([-v[1],v[0]]);flow.append(np.array([p.x,p.y])+n*8*math.sin(s/145))
add(LineString(flow).buffer(7).intersection(coast),'river-water',name='Turia · hilo de agua conceptual')
for side in [-77,77]:
 bankroad=cauce.offset_curve(side).intersection(coast)
 add(bankroad,'expressway',name='V-30 · margen '+('norte' if side>0 else 'sur'),ref='V-30',source='Márgenes del nuevo cauce recompuestas a partir del corredor OSM')
record('Nuevo cauce del Turia / Plan Sur',cauce,note='Separa la ciudad compacta del paisaje meridional. Lecho, taludes, hilo de agua, puentes y V-30 en las márgenes. Anchos y caudales de diseño; no es una simulación hidráulica.')
# Rigid city ensembles have already been packed clear of the floodway.
# Never move an individual hospital/building away from its retained block.
# Only designated crossings cross the bed at ground-level in this draft.
removed_buildings=0
for f in list(fs):
 p=f['properties'];g=shape(f['geometry'])
 if p['kind']=='building' and g.intersects(embankment):
  assert not p.get('rigid_block'), 'Rigid block conflicts with floodway'
  fs.remove(f);removed_buildings+=1
 elif p['kind'] in ['retained-road','new-road'] and g.intersects(bed):f['geometry']=mapping(g.difference(bed.buffer(8)))
for fraction,name in [(.21,'Acceso oeste'),(.41,'Patraix / Jesús'),(.62,'Malilla / sur'),(.82,'Arts / puerto')]:
 s=cauce.length*fraction;p=cauce.interpolate(s);a=cauce.interpolate(s-10);b=cauce.interpolate(s+10);v=np.array([b.x-a.x,b.y-a.y]);v/=np.linalg.norm(v);n=np.array([-v[1],v[0]]);g=LineString([np.array([p.x,p.y])-n*110,np.array([p.x,p.y])+n*110]);add(g,'new-road',name='Puente · '+name,source='Cruce de diseño');add(g,'bridge',name='Puente · '+name)
# Curve-derived spurs. Endpoints are selected on the backbone, not arbitrary cardinal grid points.
from scipy.interpolate import PchipInterpolator
def curve(points):
 p=np.asarray(points,float);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];q=np.unique(np.r_[np.linspace(0,t[-1],max(12,int(t[-1]/12))),t]);return LineString(np.column_stack([PchipInterpolator(t,p[:,i])(q) for i in (0,1)]))
for name,pts in [('Enlace A-7 / V-30',[[-2800,-100],[-2730,-170],[-2660,-190],[-2600,-100]]),('Acceso Chelva',[[-1050,2670],[-1110,2730],[-1000,2800]]),('Puerto / nuevo cauce',[[2300,-1600],[2390,-1440],[2310,-1160],[2130,-730]])]:add(curve(pts),'new-road',name=name,source='Enlace local reconstruido; tangentes ajustables')
# The real-derived airport footprint has priority over independent city/block packing.
airport_footprint=shape(json.load(open(D/'airport-layout.json'))['footprint'])
for f in list(fs):
 p=f['properties'];g=shape(f['geometry'])
 if p['kind']=='building' and not p.get('airport') and g.intersects(airport_footprint.buffer(12)):fs.remove(f)
 elif p['kind'] in ['water','green'] and g.intersects(airport_footprint):f['geometry']=mapping(g.difference(airport_footprint.buffer(16)))
 elif p['kind']=='new-road' or p['kind']=='retained-road' and p.get('city',False):
  if g.intersects(airport_footprint):f['geometry']=mapping(g.difference(airport_footprint.buffer(16)))
# A-7 is a western bypass; verify it does not cross the shortened runway.
runway=next(shape(f['geometry']) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway')
for f in list(fs):
 p=f['properties'];g=shape(f['geometry'])
 if p['kind']=='building' and not p.get('airport') and g.intersects(runway.buffer(55)):fs.remove(f)
 elif p['kind'] in ['retained-road','new-road'] and g.intersects(runway.buffer(100)):f['geometry']=mapping(g.difference(runway.buffer(110)))
fs=[f for f in fs if not shape(f['geometry']).is_empty]
from airport_access import add_airport_access
airport_review=add_airport_access(D,fs,landmarks,coast,runway,bed,routes,tr,add,record,curve)
from interior import add_interior
reservoir,interior_review=add_interior(D,fs,landmarks,coast,runway,bed,routes,tr,add,record,curve)
# Horta Sud: connect compact towns and industrial areas without urbanising the wetland.
for name,pts in [
 ('CV-400 · Sedaví / Alfafar / Catarroja',[[-600,-950],[-750,-1220],[-740,-1580],[-850,-1910],[-680,-2200],[-620,-2700]]),
 ('Sedaví / València',[[-600,-950],[-480,-760],[-470,-560],[-250,-340]]),
 ('Castellar / Mercavalència',[[220,-1380],[410,-1050],[660,-930],[1050,-820]]),
 ('Mercavalència / puerto',[[1050,-820],[1370,-940],[1650,-840],[1900,-670],[2130,-730]]),
 ('Castellar / huerta / Sedaví',[[220,-1380],[-40,-1150],[-330,-1040],[-600,-950]]),
 ('Catarroja / puerto de la Albufera',[[-620,-2700],[-430,-2490],[-350,-2200],[-100,-2080],[300,-1990]]),
 ('Pinedo / El Saler',[[2180,-1910],[2100,-1770],[1950,-1710],[1850,-1750]])]:
 g=curve(pts);water=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind'] in ['lake','reservoir']])
 if not coast.covers(g) or g.intersects(water):continue
 add(g,'new-road',name=name,source='Conexión de diseño entre sectores OSM; jerarquía inspirada en l’Horta Sud')
 cross=g.intersection(bed.buffer(20))
 if not cross.is_empty:add(cross,'bridge',name='Puente · '+name)
# Broad marshland reads as protected wetland, not empty building land.
wetland=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='lake']).buffer(210).intersection(coast).difference(bed.buffer(50))
wetland=wetland.difference(unary_union([shape(f['geometry']).buffer(20) for f in fs if f['properties']['kind'] in ['building','retained-road','new-road']]))
add(wetland,'wetland',name='Parque natural de l’Albufera · transición de marjal',source='Franja de hábitat propuesta; no límite administrativo ni inventario ecológico')
# Replace inland copies of the seafront promenade with one following the actual island shore.
import unicodedata
def plain(text):return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')
fs=[f for f in fs if not(f['properties']['kind']=='beach') and not(f['properties']['kind']=='retained-road' and any(w in plain(f['properties'].get('name','')) for w in ['passeig maritim','paseo maritimo']))]
beach_report=[]
def shore_segment(north,south):
 points=[]
 for y in np.linspace(north,south,int((north-south)/25)+1):
  cut=coast.intersection(LineString([(-5000,y),(5000,y)]))
  if not cut.is_empty:points.append([cut.bounds[2],y])
 return LineString(points)
for name,north,south,zone in [('Port Saplaya',3150,2700,'valencia'),('Patacona / Malvarrosa',2700,950,'valencia'),('Cabanyal / Arenas',950,350,'valencia'),('Saler / Devesa',-1900,-3300,'albufera')]:
 shore=shore_segment(north,south);beach=shore.offset_curve(-55).buffer(55,cap_style=2).intersection(coast);prom=shore.offset_curve(-117).intersection(coast)
 add(beach,'beach',name=name,source='Playa sobre la orilla de diseño')
 add(prom.buffer(7),'promenade-surface',name='Paseo marítimo · '+name)
 add(prom,'promenade',name='Paseo marítimo · '+name,source='Trazado pegado al borde terrestre de la playa')
 record('Paseo marítimo · '+name,prom,zone,note='Paseo situado junto al borde de la arena, siguiendo la costa de la isla. Separado del vial de vehículos.')
 beach_report.append({'name':name,'promenade_to_sand_m':prom.distance(beach),'promenade_inside_island':coast.covers(prom),'beach_area_m2':beach.area})
 for l in landmarks:
  if l['name']=='Playa · '+name:l['xy']=list(beach.representative_point().coords[0])
 # A small number of access streets connects retained urban streets to the promenade.
 if zone=='valencia':
  urbanlines=[shape(f['geometry']) for f in fs if f['properties']['kind']=='retained-road' and f['properties'].get('city',False)]
  urbanline=unary_union(urbanlines)
  for fraction in [.25,.75]:
   b=prom.interpolate(fraction,normalized=True);a=nearest_points(urbanline,b)[0]
   if a.distance(b)<900:add(curve([[a.x,a.y],[(a.x+b.x)/2,a.y],[b.x,b.y]]),'new-road',name='Acceso a playa · '+name,source='Enlace de diseño')
# After moving the city east, retain a clear beach/promenade strip at the water's edge.
coastal_strip=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind'] in ['beach','promenade-surface']])
for f in list(fs):
 p=f['properties'];g=shape(f['geometry'])
 if p['kind']=='building' and g.intersects(coastal_strip):fs.remove(f)
 elif p['kind']=='retained-road' and p.get('roadclass') not in ['footway','path','steps','pedestrian','cycleway'] and g.intersects(coastal_strip):f['geometry']=mapping(g.difference(coastal_strip))
# Calpe's beach follows the southern shore, never an inland copy of the source coast.
south_points=[]
for x in np.linspace(650,1750,65):
 cut=coast.intersection(LineString([(x,-6000),(x,-3500)]));south_points.append([x,cut.bounds[1]])
shore=LineString(south_points);beach=shore.offset_curve(50).buffer(50,cap_style=2).intersection(coast);prom=shore.offset_curve(107)
add(beach,'beach',name='Calpe · frente litoral compacto',source='Playa sobre la orilla sur de la isla');add(prom.buffer(7),'promenade-surface',name='Paseo marítimo · Calpe');add(prom,'promenade',name='Paseo marítimo · Calpe');record('Playa y paseo de Calpe',beach,'sur')
for l in landmarks:
 if l['name']=='Calpe · puerto y paseo':l['xy']=list(prom.interpolate(.8,normalized=True).coords[0]);l['retention']='Frente litoral trasladado a la costa sur de la isla. Puerto detallado pendiente; paseo conectado a la playa.'
calpe_roads=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='retained-road' and not shape(f['geometry']).is_empty and shape(f['geometry']).centroid.y<-3800])
b=prom.interpolate(.3,normalized=True);a=nearest_points(calpe_roads,b)[0];g=curve([list(a.coords)[0],[(a.x+b.x)/2+35,(a.y+b.y)/2],list(b.coords)[0]])
if coast.covers(g):add(g,'new-road',name='Calpe · acceso al paseo de playa',source='Enlace de diseño entre casco OSM y orilla')
beach_report.append({'name':'Calpe','promenade_to_sand_m':prom.distance(beach),'promenade_inside_island':coast.covers(prom),'beach_to_coast_m':beach.distance(coast.boundary),'beach_area_m2':beach.area})
for item in beach_report:
 if 'beach_to_coast_m' not in item:
  bg=next(shape(f['geometry']) for f in fs if f['properties']['kind']=='beach' and f['properties'].get('name')==item['name']);item['beach_to_coast_m']=bg.distance(coast.boundary)
# Give Port Saplaya an explicit marine entrance through the compact shoreline strip.
marina=next((shape(f['geometry']) for f in fs if f['properties']['kind']=='water' and shape(f['geometry']).centroid.y>2300 and shape(f['geometry']).centroid.x>1800),None)
if marina is not None:
 a=marina.representative_point();b=shore_segment(a.y+1,a.y-1).interpolate(.5,normalized=True);channel=curve([[a.x,a.y],[a.x+170,a.y-30],[b.x,b.y]]).buffer(22).intersection(coast);add(channel,'water',name='Entrada marítima · Port Saplaya',source='Canal de diseño; boca compactada')
 for f in fs:
  if f['properties']['kind']=='beach':f['geometry']=mapping(shape(f['geometry']).difference(channel))
 # Explicit crossing of the shoreline promenade over the marina entrance.
 for f in fs:
  if f['properties']['kind']=='promenade':
   cross=shape(f['geometry']).intersection(channel.buffer(5))
   if not cross.is_empty:add(cross,'bridge',name='Puente del paseo · Port Saplaya')
(D/'beach-review.json').write_text(json.dumps(beach_report,indent=2,ensure_ascii=False))
# Recompose park edges in the remaining open ground, retaining every block.
block_interior=unary_union([shape(f['geometry']).buffer(-5) for f in fs if f['properties']['kind']=='city-block'])
for f in fs:
 if f['properties']['kind']=='designed-park':f['geometry']=mapping(shape(f['geometry']).difference(block_interior))
# Urban texture is derived from the retained street/building fabric, not generic monument circles.
urbanroads=[shape(f['geometry']) for f in fs if f['properties']['kind']=='retained-road' and f['properties'].get('roadclass') in ['residential','living_street','tertiary','secondary','primary']]
urban=unary_union(urbanroads).buffer(28).buffer(10).difference(embankment).intersection(coast)
add(urban,'urban-area',name='Tejido urbano seleccionado')
# Named ordinary OSM amenities are kept as searchable references, with source IDs.
blockdec=json.load(open(D/'manzanas-decision.geojson'))['features'];kept=[shape(f['geometry']) for f in blockdec if f['properties']['action']=='retener'];ktree=STRtree(kept);pois=[];seen=set();nodes=json.load(open(D/'osm-nodes.json'));sectors=json.load(open(D/'sectors.json'))
for o in nodes:
 t=o['tags'];name=t.get('name','');amenity=t.get('amenity');natural=t.get('natural');g=transform(tr,shape(o['geometry']));pt=g.representative_point();dest=None;zone='valencia'
 if not name or amenity not in ['school','hospital','clinic','marketplace','library','university','townhall','sports_centre','police','fire_station','place_of_worship','community_centre','bus_station','fountain'] and t.get('railway') not in ['station','tram_stop'] and natural not in ['peak','spring']:continue
 rel=Point(pt.x-origin[0],pt.y-origin[1])
 if len(ktree.query(rel,predicate='intersects')):
  x,y=warp(rel.x,rel.y);dest=[float(x),float(y)]
 else:
  for s in sectors:
   if shape(s['source_mask']).covers(pt):
    sx,sy=tr(*s['source']);dest=[pt.x+s['dest'][0]-sx,pt.y+s['dest'][1]-sy];zone=s['zone'];break
 if dest is None or not coast.covers(Point(dest)) or bed.covers(Point(dest)) or (name,round(dest[0]/30),round(dest[1]/30)) in seen:continue
 seen.add((name,round(dest[0]/30),round(dest[1]/30)))
 category='Universidades' if amenity=='university' else 'Naturaleza' if natural else 'Transporte' if t.get('railway') or amenity=='bus_station' else 'Vida cotidiana'
 pois.append({'id':o['id'],'name':name,'xy':dest,'zone':zone,'category':category,'osm':'node/'+o['id'][1:],'retention':'Referencia cotidiana de OSM trasladada al tejido seleccionado. No se ha verificado el funcionamiento actual del establecimiento.'})
# Named retained buildings add references at their actual proposed footprints.
known={p['id'] for p in pois}|{l['id'] for l in landmarks}
for f in fs:
 pr=f['properties'];osm=pr.get('osm');name=pr.get('name','')
 if pr['kind']!='building' or not osm or not name:continue
 ident=('w' if osm.startswith('way/') else 'r')+osm.split('/')[-1]
 if ident in known:continue
 pt=shape(f['geometry']).representative_point();known.add(ident)
 pois.append({'id':ident,'name':name,'xy':[pt.x,pt.y],'zone':pr.get('zone','valencia'),'category':'Vida cotidiana','osm':osm,'retention':'Edificio OSM retenido; ubicación de diseño sobre su huella trasladada.'})
(D/'pois.json').write_text(json.dumps(pois,ensure_ascii=False))
# Multi-scale relief and explicit contour geometry improve terrain readability.
H=np.load(D/'height-base.npy');terrain=json.load(open(D/'terrain.json'));E=terrain['extent'];N=terrain['size'];X,Y=np.meshgrid(np.linspace(E[0],E[2],N),np.linspace(E[3],E[1],N));land=contains_xy(coast,X,Y);rng=np.random.default_rng(220)
noise=gaussian_filter(rng.standard_normal(H.shape),9);noise/=noise.std();micro=gaussian_filter(rng.standard_normal(H.shape),2);micro/=micro.std();H=np.maximum(0,H*(1+.12*noise+.025*micro));H[contains_xy(embankment,X,Y)]=5;H[~land]=0
# Reservoir sits in a designed inland valley at a constant level.
inside_reservoir=contains_xy(reservoir,X,Y);margin=contains_xy(reservoir.buffer(90),X,Y);blend=gaussian_filter(margin.astype(float),4);H=H*(1-blend)+np.maximum(H,170)*blend;H[inside_reservoir]=155
# A broad airport plain is applied after all terrain/noise passes, at a single design elevation.
airport_ground=shape(json.load(open(D/'airport-layout.json'))['footprint']);airport_plain=airport_ground.buffer(180);plain_mask=contains_xy(airport_plain,X,Y);blend=gaussian_filter(plain_mask.astype(float),9);H=H*(1-blend)+18*blend;H[plain_mask]=18;H[inside_reservoir]=155
# All open water remains level. Ridge contours are based on this same final DEM.
for f in fs:
 if f['properties']['kind'] in ['lake','water']:H[contains_xy(shape(f['geometry']),X,Y)]=0
np.save(D/'height.npy',H.astype('float32'));Image.fromarray(np.rint(H*10).astype('uint16')).save(D/'altura-decimetros.png')
cmap=LinearSegmentedColormap.from_list('isla',['#789a6f','#708e57','#8b925c','#aca078','#d5c7a2']);rgb=LightSource(315,45).shade(H,cmap,vert_exag=1.2,dx=11,dy=14,blend_mode='soft');rgb[:,:,3]=land.astype(float);Image.fromarray((rgb*255).astype('uint8')).save(D/'relieve.png')
fig,ax=plt.subplots();cont=ax.contour(X,Y,H,levels=[60,100,150,200,300,400,500,600,700])
for h,parts in zip(cont.levels,cont.allsegs):
 for c in parts:
  if len(c)>3:add(LineString(c).simplify(5).intersection(coast),'contour',height=int(h))
forest=ax.contourf(X,Y,np.where((H>65)&(H<530)&(noise>-.3)&(~inside_reservoir),1,0),levels=[.5,1.5])
for poly in forest.get_paths():
 for vertices in poly.to_polygons():
  if len(vertices)<4:continue
  g=make_valid(Polygon(vertices)).intersection(coast)
  if g.area>8000:add(g,'forest',name='Cobertura forestal de diseño',source='Distribución propuesta; no inventario ecológico real')
plt.close(fig)
from circuit_layout import recompose_circuit
metrics['f1_design_m']=recompose_circuit(D,fs,coast,landmarks)
# Join retained components through free ground, without deleting intact buildings.
from street_network import finish_network
fixes, network_fixes = finish_network(D,fs,coast,add)
cs=components(fs);main=cs[0]['geometry'];total=sum(c['length_m'] for c in cs)
network={'planar_component_count':len(cs),'main_component_length_m':cs[0]['length_m'],'total_drivable_line_length_m':total,'main_component_fraction':cs[0]['length_m']/total,'short_connections_added':fixes,'repair':network_fixes,'note':'Planar noding at1m precision; does not validate grade separation, turn restrictions or driving navigation.','landmark_distance_to_main_road_m':{l['name']:round(main.distance(Point(l['xy'])),1) for l in landmarks}}
(D/'network-review.json').write_text(json.dumps(network,indent=2,ensure_ascii=False))
cityroads=[shape(f['geometry']) for f in fs if f['properties']['kind']=='retained-road' and f['properties'].get('city',False)]
cityground=unary_union(cityroads).buffer(25).intersection(coast)
metrics['valencia_urban_footprint_km2']=cityground.area/1e6
metrics['valencia_urban_envelope_km2']=unary_union(cityroads).convex_hull.area/1e6
metrics.update({'reservoir_area_km2':interior_review['design_area_km2'],'secondary_routes':len(interior_review['secondary_routes']),'secondary_length_km':interior_review['secondary_length_km'],'chelva_coast_distance_m':interior_review['chelva_coast_distance_m'],'continuous_highway_corridors':len(configs),'corridor_details':corridorlog,'new_turia_cauce_m':cauce.length,'osm_everyday_pois':len(pois),'buildings_removed_for_floodway':removed_buildings,'a7_runway_clearance_m':routes['A-7'].distance(runway),'road_main_component_fraction':network['main_component_fraction'],'city_buildings_final':sum(f['properties']['kind']=='building' and f['properties'].get('rigid_block',False) for f in fs)})
fs=[f for f in fs if not shape(f['geometry']).is_empty]
from street_labels import prepare_names
prepare_names(fs)
(D/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));(D/'landmarks.json').write_text(json.dumps(landmarks,ensure_ascii=False));(D/'isla-metros.geojson').write_text(json.dumps({'type':'FeatureCollection','coordinate_system':'LOCAL_METRES_FICTIONAL','features':fs},ensure_ascii=False,separators=(',',':')));(D/'continuous-corridors.geojson').write_text(json.dumps({'type':'FeatureCollection','features':comparisons}));(D/'corridor-review.json').write_text(json.dumps(corridorlog,indent=2))
print('FEATURES',len(fs),'POIS',len(pois),'CAUCE',round(cauce.length),'A7/runway',round(routes['A-7'].distance(runway)),'MAIN NETWORK',network['main_component_fraction'])
