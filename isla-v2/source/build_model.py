"""Nonuniform block removal and seam closure; original geometries remain traceable.
Local design coordinates are metres, NOT geographic coordinates of Valencia.
"""
import json,pathlib,math,collections,unicodedata
import numpy as np
from shapely.geometry import shape,mapping,Point,LineString,Polygon,box
from shapely.ops import transform,unary_union,polygonize,nearest_points
from shapely.affinity import translate,scale,rotate
from shapely import make_valid,STRtree,contains_xy,segmentize
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter,distance_transform_edt
from pyproj import Transformer
from PIL import Image
from matplotlib.colors import LightSource,LinearSegmentedColormap
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';OLD=D/'reference-landmarks'
tr=Transformer.from_crs(4326,25830,always_xy=True).transform;origin=tr(-.377,39.4735)
def utm(g):return transform(tr,shape(g))
def rel(g):return translate(utm(g),-origin[0],-origin[1])
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
raw=json.load(open(D/'osm-selection.json'));nodes=json.load(open(D/'osm-nodes.json'));lookup={x['id']:x for x in raw+nodes}
for fn in ['landmark-candidates.json','additions.json','extra-landmarks.json']:
 for c in json.load(open(OLD/fn)):lookup.setdefault(c['id'],c)
features=[];landmarks=[];retainedids=set();stats=collections.Counter();samples=[]
def add(g,kind,**p):
 if g.is_empty:return
 if not g.is_valid:g=make_valid(g)
 if g.is_empty:return
 features.append({'type':'Feature','geometry':mapping(g),'properties':{'kind':kind,**p}})
def osmurl(id):return {'n':'node/','w':'way/','r':'relation/'}[id[0]]+id[1:]
def lm(name,xy,zone='valencia',id=None,g=None,note='Propuesta de posición en la isla; no ubicación geográfica real.',original=None):
 id=id or 'design-'+str(len(landmarks));o=lookup.get(id);area=utm(o['geometry']).area if o else 0
 landmarks.append({'id':id,'name':name,'xy':list(xy),'zone':zone,'retention':note,'osm':osmurl(id) if o else None,'area_before_m2':area,'area_after_m2':g.area if g is not None else 0})
 if g is not None and g.geom_type not in ['Point','MultiPoint']:add(g,'landmark-footprint',name=name,id=id,source=note)
 return landmarks[-1]
# Envelope includes inland waters and the harbour. This conservative measure avoids double counting.
coast=Polygon([(-4100,1400),(-3400,3300),(-2800,4600),(-1300,5000),(0,4600),(1100,4200),(2300,3500),(3200,2700),(3100,1800),(3300,800),(3500,-200),(3400,-1200),(2900,-1900),(2600,-3000),(2400,-4000),(2800,-4900),(2100,-5600),(1200,-5300),(300,-5900),(-600,-5400),(-1700,-4500),(-2300,-3200),(-3600,-2600),(-4100,-1500),(-3700,-300),(-4200,600)])
coast=coast.buffer(110,join_style=1).buffer(-110,join_style=1)
coast=scale(coast,xfact=(49e6/coast.area)**.5,yfact=(49e6/coast.area)**.5,origin=(0,0))
add(coast,'coast',name='Isla Levante · envolvente 49 km²')
# Select whole OSM blocks; retain their real dimensions and internal street graph.
from block_city import build_city
blocks,keep,removed,warp=build_city(D,raw,lookup,rel,coast,add,lm,stats,retainedids)
from compaction import XS,YS,OFFSET,diagnostics
cityids=__import__('block_city').IDS
from shapely import STRtree
ktree=STRtree(keep)
def xy(lon,lat):
 x,y=tr(lon,lat);a,b=warp(x-origin[0],y-origin[1]);return [float(a),float(b)]
for name,ll in [('Plaça de Patraix',(-.3961,39.4595)),('Campanar · núcleo y plaza',(-.4024,39.4877)),('Torrefiel · mercado y residencial',(-.3769,39.4948)),('Benimaclet · plaza y estación',(-.3625,39.4857)),('UV · campus Blasco Ibáñez',(-.3608,39.4795)),('UPV · campus de Vera / Ágora',(-.3435,39.4814)),('Alboraia · núcleo y mercado',(-.3500,39.5009)),('Cabanyal · trama marítima',(-.3316,39.4704)),('Natzaret · barrio portuario',(-.3324,39.4473)),('Malilla · tejido residencial',(-.3763,39.4518))]:lm(name,xy(*ll),note='Referencia trasladada junto a su grupo de manzanas reales; las manzanas no se escalan.')
# Town sectors are polygons enclosing street sequences, not radial monument buffers.
sectors=[]
def sector(id,name,zone,center,dest,outline,build=True):
 src=tr(*center);mask=Polygon([(src[0]+x,src[1]+y) for x,y in outline]);dx=dest[0]-src[0];dy=dest[1]-src[1]
 sectors.append({'id':id,'name':name,'zone':zone,'source':center,'dest':dest,'source_mask':mapping(mask)})
 for o in raw:
  gg=shape(o['geometry']);p=gg.representative_point()
  if abs(p.x-center[0])>.025 or abs(p.y-center[1])>.025:continue
  g=utm(o['geometry']);t=o['tags']
  if not g.is_valid:g=make_valid(g)
  if not mask.intersects(g):continue
  if t.get('building') and build and mask.covers(g):
   ng=translate(g,dx,dy)
   if coast.covers(ng):add(ng,'building',height=6,name=t.get('name',''),osm=osmurl(o['id']),zone=zone,sector=id,source='OSM · edificio entero trasladado')
  elif t.get('highway') and g.geom_type in ['LineString','MultiLineString']:
   ng=translate(g.intersection(mask),dx,dy).intersection(coast)
   add(ng,'retained-road',name=t.get('name',''),id=o['id'],roadclass=t['highway'],sector=id,source='OSM · curvas y cruces trasladados 1:1');retainedids.add(o['id'])
  elif t.get('landuse') in ['industrial','commercial','farmland','orchard','greenhouse_horticulture'] and g.geom_type in ['Polygon','MultiPolygon']:
   add(translate(g.intersection(mask),dx,dy).intersection(coast),'industrial' if t['landuse'] in ['industrial','commercial'] else 'agriculture',name=t.get('name',t['landuse']),source='OSM · uso del suelo trasladado',osm=osmurl(o['id']))
  elif (t.get('natural') in ['water','beach'] or t.get('leisure') in ['park','garden']) and g.geom_type in ['Polygon','MultiPolygon']:
   add(translate(g.intersection(mask),dx,dy).intersection(coast),'water' if t.get('natural')=='water' else 'beach' if t.get('natural')=='beach' else 'green')
 add(translate(mask,dx,dy).intersection(coast),'patch',name=name,sector=id,source='Sector de secuencias urbanas; límite de selección, no isla circular')
 return lambda g:translate(g,dx,dy)
chelv=sector('chelva','Chelva · casco y barrios','chelva',(-.997,39.747),(-1000,2800),[(-420,-260),(-450,50),(-180,310),(150,320),(460,130),(390,-210),(100,-350)])
cofr=sector('cofrentes','Cofrentes · pueblo y castillo','cofrentes',(-1.0628,39.23),(-2450,-700),[(-300,-200),(-380,80),(-150,320),(160,300),(360,80),(280,-240)])
jalan=sector('jalance','Jalance · núcleo','cofrentes',(-1.077,39.1915),(-2180,-2630),[(-220,-200),(-270,90),(-80,250),(220,140),(230,-150)])
saler=sector('saler','El Saler','albufera',(-.3327,39.383), (1850,-1750),[(-260,-170),(-190,200),(180,270),(300,0),(140,-200)])
palmar=sector('palmar','El Palmar','albufera',(-.3176,39.3115),(1400,-3270),[(-170,-270),(-180,150),(50,300),(190,140),(170,-260)])
calpe=sector('calpe','Calpe · pequeña muestra del casco','sur',(.0445,38.6444),(850,-4320),[(-220,-180),(-250,70),(-50,210),(230,120),(270,-160)])
# Saplaya retains its marina form and neighbouring residential waterfront.
alb=sector('alboraia','Alboraia · núcleo compacto','valencia',(-.3500,39.501),(1500,2350),[(-220,-170),(-230,140),(-90,250),(200,210),(240,-150)])
sap=sector('saplaya','Port Saplaya','valencia',(-.3205,39.5105),(2100,2650),[(-280,-370),(-350,100),(-160,330),(210,330),(310,-270)])
# Palmar architecture requested at full size, using the same rigid town translation.
required=json.load(open(D/'required-landmarks.json'));barracas=next(v for v in required if v['index']==96);source_areas={o['id']:o for o in json.load(open(D/'required-landmark-sources.json'))};placed=[];placement=json.load(open(D/'landmark-placement.json'))
for id in barracas['source_ids']:
 o=source_areas[id];lookup[id]=o;g=utm(o['geometry']);ng=palmar(g);placed.append(ng);src=rel(o['geometry']);delta=[ng.centroid.x-src.centroid.x,ng.centroid.y-src.centroid.y]
 add(ng,'protected-landmark',source_id=id,source_area_m2=src.area,area_m2=ng.area,scale=1,delta=delta,city=False)
 add(ng,'building',name=barracas['name'],osm=osmurl(id),height=6,height_source='Vista previa; altura sin verificar',source_area_m2=src.area,rigid_block=True,zone='albufera',source='OSM · barraca completa a escala 1:1')
 placement.append({'id':id,'source_area_m2':src.area,'area_m2':ng.area,'delta':delta,'height_m':6,'height_source':'Preview only; height not documented'})
if placed:
 ng=unary_union(placed);l=lm(barracas['name'],ng.representative_point().coords[0],'albufera',id=barracas['source_ids'][0],g=ng,note='Conjunto de barracas OSM de El Palmar, trasladadas a tamaño real con el pueblo.');l.update({'required_index':96,'source_ids':barracas['source_ids'],'scale':1,'area_before_m2':ng.area})
(D/'landmark-placement.json').write_text(json.dumps(placement,ensure_ascii=False,indent=2))
# Campus boundaries group retained full-size blocks; no miniature campus buildings.
for id,name in [('w143429087','Universitat de València · Campus dels Tarongers'),('w147062296','Universitat de València · campus educativo')]:
 g=rel(lookup[id]['geometry']);pieces=[]
 for f in json.load(open(D/'city-blocks.geojson'))['features']:
  dst=shape(f['geometry']);dx,dy=f['properties']['delta'];src=translate(dst,-dx,-dy)
  if src.intersects(g):pieces.append(dst)
 ng=unary_union(pieces)
 if not ng.is_empty:lm(name,ng.representative_point().coords[0],id=id,g=ng,note='Campus recompuesto con sus manzanas seleccionadas a escala real.')
# Bioparc remains a landscape reference; unlike requested architecture, its park extent is reinterpreted.
lm('Bioparc València · parque recompuesto',xy(-.407,39.478),note='Referencia del parque; recinto recompuesto, no huella arquitectónica certificada.')
# Southern transition: industrial halls, compact town samples, then protected wetland.
for sid,name,zone,src,dest,outline in [
 ('mercavalencia','Mercavalència · mercado y logística','valencia',(-.3509,39.4344),(1050,-820),[(-280,-200),(-300,150),(-100,260),(320,230),(330,-170)]),
 ('sedavi','Sedaví · núcleo y borde industrial','albufera',(-.3845,39.4260),(-600,-950),[(-170,-160),(-210,90),(-70,210),(180,170),(220,-100)]),
 ('alfafar','Alfafar · núcleo compacto','albufera',(-.3960,39.4180),(-850,-1910),[(-180,-170),(-210,100),(-20,200),(200,130),(210,-150)]),
 ('catarroja','Catarroja · acceso a la marjal','albufera',(-.4033,39.4033),(-620,-2700),[(-180,-170),(-210,110),(40,230),(210,130),(180,-190)]),
 ('castellar','Castellar · núcleo de huerta','albufera',(-.3557,39.4234),(220,-1380),[(-120,-110),(-150,90),(20,160),(150,100),(160,-80)]),
 ('pinedo','Pinedo · fachada del parque','albufera',(-.3325,39.4201),(2180,-1910),[(-120,-130),(-160,60),(-20,160),(150,100),(140,-130)])]:
 sector(sid,name,zone,src,dest,outline);lm(name,dest,zone,note='Muestra de tejido OSM trasladada íntegra: edificios y calles locales a tamaño original; se omite el resto del municipio.')
sector('huerta-sur','Huerta de transición sur','albufera',(-.3730,39.4180),(-100,-1900),[(-260,-270),(-290,190),(120,260),(230,40),(170,-250)],build=False)
sector('marjal-oeste','Marjal occidental · parcelas y acequias','albufera',(-.375,39.399),(-110,-2780),[(-230,-400),(-260,260),(130,320),(210,-200)],build=False)
for l in landmarks:
 if l['name']=='Alboraia · núcleo y mercado':l['xy']=[1500,2350]
for i,fn,z,name in [('w418122519',chelv,'chelva','Chelva · iglesia de los Ángeles'),('w545472804',chelv,'chelva','Palacio vizcondal'),('w179718813',cofr,'cofrentes','Castillo de Cofrentes'),('w244598148',jalan,'cofrentes','Castillo de Jalance'),('r2169641',sap,'valencia','Port Saplaya · marina')]:
 g=fn(utm(lookup[i]['geometry']));lm(name,g.representative_point().coords[0],z,i,g,'Geometría OSM íntegra trasladada junto a calles y edificios del sector.')
# Independent site footprints; no disks of surrounding city.
def place_site(i,dest,name,zone='valencia',kind=None):
 g=utm(lookup[i]['geometry']);c=g.representative_point();ng=translate(g,dest[0]-c.x,dest[1]-c.y)
 lm(name,dest,zone,i,ng,'Pieza OSM íntegra trasladada; distancia a los núcleos reducida.')
 if kind:add(ng,kind,name=name)
 return ng
central=place_site('w126986991',(-2400,-1710),'Central nuclear de Cofrentes','cofrentes','industrial')
# Preserve plant OSM buildings within actual site bounds, using same translation.
origcentral=utm(lookup['w126986991']['geometry']);cc=origcentral.representative_point()
for o in raw:
 if not o['tags'].get('building'):continue
 p=shape(o['geometry']).representative_point()
 if not(-1.07<p.x<-1.035 and 39.2<p.y<39.23):continue
 g=utm(o['geometry'])
 if origcentral.intersects(g):add(translate(g,-2400-cc.x,-1710-cc.y),'building',height=24,name=o['tags'].get('name',''),zone='cofrentes',source='OSM · recinto central')
# Bonaire: keep main building; delete most peripheral parking land.
bon=place_site('r8404254',(-2450,100),'Bonaire · edificio principal') if 'r8404254' in lookup else place_site('w150145567',(-2450,100),'Bonaire · centro comercial')
add(bon.buffer(45),'industrial',name='Bonaire · aparcamiento reducido')
# Airport retains real OSM runway, taxiways, apron and terminal relations.
from airport_model import build_airport
runway,terminal,airport_ground=build_airport(D,raw,lookup,utm,coast,add,lm)
# Natural coastline / lagoon reinterpreted as continuous landscapes, never circular town cut-outs.
lake=Polygon([(350,-1750),(650,-1660),(950,-1740),(1210,-1700),(1510,-1900),(1700,-2240),(1690,-2520),(1540,-2850),(1290,-3090),(1000,-2990),(780,-3100),(480,-2920),(300,-2630),(220,-2390),(360,-2180),(290,-1940)]).buffer(50).buffer(-50)
add(lake,'lake',name='Albufera · orilla reinterpretada')
lm('L’Albufera · laguna y marjal',list(lake.centroid.coords[0]),'albufera',id='r2786392',g=None,note='Laguna reinterpretada: se elimina agua abierta, conservando marjal, devesa, pueblos y canales como secuencia. Contorno de diseño, no réplica reducida.')
for name,p in [('El Saler',(1850,-1750)),('El Palmar',(1400,-3270)),('Embarcadero del Palmar',(1330,-3040)),('Port de Catarroja',(300,-1990)),('Gola de Pujol',(1810,-2580))]:lm(name,p,'albufera')
# Turia spine follows original park meanders reconstructed from geographic waypoints.
turia_ll=[(-.421,39.484),(-.411,39.479),(-.403,39.478),(-.394,39.479),(-.383,39.481),(-.376,39.480),(-.369,39.478),(-.363,39.474),(-.358,39.468),(-.352,39.461),(-.347,39.456),(-.340,39.451)]
def smooth(points):
 p=np.asarray(points,float);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];q=np.unique(np.r_[np.linspace(0,t[-1],max(25,int(t[-1]/20))),t]);return LineString(np.column_stack([PchipInterpolator(t,p[:,i])(q) for i in (0,1)]))
turia=smooth([xy(*p) for p in turia_ll]);add(turia.buffer(55),'designed-park',name='Jardí del Túria · corredor recompuesto')
lm('Jardí del Túria · corredor y puentes',list(turia.interpolate(.5,normalized=True).coords[0]),note='Secuencia del antiguo cauce conservada con meandros recompuestos. No representa el nuevo cauce meridional.')
# Port: distinct working basins, marine gateway and a historic F1 interpretation.
portwater=Polygon([(2390,-450),(2860,-400),(2970,-750),(2800,-1250),(2480,-1330),(2390,-950)]).intersection(coast)
add(portwater,'water',name='Puerto de València · dársenas')
for poly in [[(2380,-630),(2730,-610),(2760,-740),(2400,-790)],[(2420,-960),(2830,-890),(2850,-1010),(2470,-1100)],[(2910,-450),(3040,-420),(3100,-1000),(2980,-1170)]]:
 add(Polygon(poly).intersection(coast),'industrial',name='Muelles y logística portuaria')
lm('Puerto de València · muelles y dársenas',(2730,-860),note='Puerto de diseño: menos muelles y superficie, conserva la relación Marina–Grau–Natzaret y el carácter productivo.')
# Compact historic loop: design inspired by documented harbour/bridge sequence; not exact 25-turn replica.
f1=smooth([(2040,180),(2270,210),(2520,100),(2620,-80),(2510,-210),(2330,-180),(2270,-350),(2400,-480),(2310,-620),(2070,-590),(1910,-420),(1900,-190),(2040,180)])
f1=LineString(list(f1.coords)[:-1]+[f1.coords[0]])
add(f1,'circuit',name='Antiguo F1 · interpretación compacta',source='Trazado de diseño inspirado en circuito histórico; no levantamiento exacto')
lm('Antiguo circuito de Fórmula 1',list(f1.interpolate(.15,normalized=True).coords[0]),note='Bucle compacto de diseño inspirado en la secuencia del circuito histórico junto a la Marina. No reproduce todas las curvas de la vuelta de 5,419 km; ajuste de fidelidad pendiente.')
# East beaches are strips along the designed coastline with a separate port interruption.
for name,pts in [('Patacona / Malvarrosa',[(2580,2440),(2690,2020),(2660,1630),(2730,1200)]),('Cabanyal / Arenas',[(2730,1200),(2840,760),(2920,390)]),('Saler / Devesa',[(2460,-1850),(2300,-2350),(2210,-2800),(2140,-3240)])]:
 line=smooth(pts);add(line.buffer(45).intersection(coast),'beach',name=name);lm('Playa · '+name,list(line.interpolate(.5,normalized=True).coords[0]),'albufera' if 'Saler' in name else 'valencia')
# Huerta and marjal fields are non-residential transitions, oriented parcels of design.
for x,y,w,h,z in [(1100,2350,950,420,'huerta'),(450,2900,700,420,'huerta'),(-100,-2200,320,900,'marjal'),(950,-3500,800,150,'marjal')]:
 for i in range(5):
  g=box(x+i*w/5+8,y,x+(i+1)*w/5-8,y+h).intersection(coast).difference(lake)
  add(g,'agriculture',name=z)
# Natural references are located in purposeful valleys and mountain routes.
for i,dest,name,z in [('n5858594685',(-580,3260),'Acueducto de Peña Cortada','chelva'),('w496168366',(-1110,3330),'Ermita del Remedio','chelva'),('n10008253791',(-1140,3410),'Pico del Remedio','chelva'),('w438173750',(-1110,2270),'La Playeta · cascadas y remanso','chelva'),('w352916963',(-3100,-350),'Balneario de Hervideros','cofrentes'),('n11406174536',(-2780,-300),'Cerro de Agras','cofrentes')]:
 place_site(i,dest,name,z)
lm('Cascada de La Playeta',(-1120,2280),'chelva',note='Ubicación propuesta junto a la Playeta. La fuente municipal documenta cascadas; el salto se representa de forma conceptual y requiere levantamiento para modelado detallado.')
lm('Molino Puerto · Ruta del Agua',(-930,2450),'chelva')
add(LineString([(-630,3225),(-530,3295)]).buffer(5),'landmark-footprint',name='Acueducto · puente de diseño')
# Ifac retains a recognisable coastal promontory and isthmus; synthetic relief follows below.
ifac=Polygon([(1800,-4250),(1980,-4190),(2200,-4300),(2340,-4500),(2250,-4700),(2050,-4780),(1870,-4610),(1790,-4410)]).intersection(coast)
add(ifac,'rock',name='Penyal d’Ifac · relieve reinterpretado')
lm('Penyal d’Ifac / Peñón de Ifach',(2090,-4470),'sur',g=ifac,note='Promontorio e istmo reinterpretados para la isla; elevación sintética, no topografía real.')
lm('Calpe · casco y pequeño frente marítimo',(850,-4320),'sur');lm('Calpe · puerto y paseo',(1530,-4350),'sur');lm('Serra de la Safor · montañas al sur de Gandia',(-450,-4150),'sur',note='Relieve de diseño inspirado en sierra, barrancos y circo de la Safor. Se omite gran parte del territorio entre Gandia y Calpe.')
add(smooth([(1100,-4420),(1400,-4400),(1710,-4320)]).buffer(40),'beach',name='Calpe · frente litoral compacto')
# Terrain-aware connectors use curved waypoint sequences; seams elsewhere keep OSM road bends.
connections=[]
def route(name,pts,kind='new-road',source='Conexión de diseño sinuosa; no carretera real a escala'):
 g=smooth(pts).intersection(coast);add(g,kind,name=name,source=source);connections.append((name,g));return g
route('Acceso oeste / aeropuerto',[(-2390,910),(-2190,800),(-1890,820),(-1580,700),(-1280,640),(-990,680),(-700,630)])
route('Bonaire – acceso oeste',[(-2450,100),(-2640,-80),(-2730,-400),(-2600,-670),(-2420,-900)])
route('València – Chelva',[(-1280,640),(-1500,1000),(-1700,1400),(-1640,1750),(-1870,1990),(-2140,2140),(-2390,2420),(-2460,2710),(-2280,3040),(-2200,3210),(-2000,3400)])
route('Ruta del Agua / La Playeta',[(-1000, 2800), (-800, 2670), (-880, 2540), (-930, 2450), (-1090, 2390), (-1210, 2330), (-1120, 2280)],'trail')
route('Chelva – Peña Cortada',[(-800, 2670), (-560, 2820), (-670, 2980), (-500, 3120), (-580, 3260)],'trail')
route('Subida al Remedio',[(-1200, 2610), (-1390, 2840), (-1250, 2990), (-1440, 3140), (-1240, 3290), (-1320, 3420), (-1110, 3330)],'trail')
route('València – Cofrentes',[(-2450,100),(-2770,40),(-2940,-140),(-2790,-370),(-2520,-450),(-2450,-700)])
route('Valle / acceso central',[(-2450,-700),(-2190,-880),(-2110,-1120),(-2350,-1320),(-2410,-1510),(-2200,-1790)])
route('Valle – Jalance',[(-2110,-1120),(-1880,-1420),(-1970,-1780),(-1790,-2060),(-1970,-2310),(-2210,-2480),(-2180,-2630)])
route('Costa – Devesa – Calpe',[(2130,-730),(2000,-1230),(1850,-1750),(1930,-2100),(1880,-2500),(1830,-2850),(1740,-3200),(1570,-3450),(1640,-3700),(1470,-3940),(1280,-4110),(850,-4320)])
route('El Palmar / embarcadero',[(1740,-3200),(1590,-3300),(1400,-3270),(1330,-3040)])
route('Puerto de la Safor',[(-2180,-2630),(-2100,-2970),(-1590,-3130),(-1340,-3400),(-1500,-3590),(-1150,-3820),(-1000,-4090),(-680,-4230),(-460,-4050),(-220,-4300),(80,-4250),(370,-4470),(850,-4320)])
route('Calpe – puerto – Ifac',[(850,-4320),(1160,-4260),(1390,-4320),(1530,-4350),(1690,-4300),(1810,-4320)])
route('Saplaya – Alboraia',[(2100,2650),(1960,2570),(1800,2590),(1590,2460),(1400,2260),(1170,2190)])
# Designed rivers connect valleys and waterfalls; bridges tagged at road crossings below.
river1=smooth([(-1400,3150),(-1210,2840),(-930,2450),(-1120,2280),(-1400,2150),(-1550,1910),(-1800,1560)])
river2=smooth([(-3250,200),(-2900,-230),(-2600,-540),(-2260,-900),(-2280,-1170),(-2500,-1400),(-2250,-1820),(-2100,-2140),(-2240,-2550),(-2500,-2790)])
river3=smooth([(-1750,-300),(-1980,-500),(-2090,-750),(-2260,-900)])
for name,g in [('Río de Chelva',river1),('Júcar · valle recompuesto',river2),('Cabriel · confluencia',river3)]:add(g.buffer(16).intersection(coast),'river-water',name=name)
add(smooth([(1690,-2520),(1810,-2580),(2180,-2570)]).buffer(12),'river-water',name='Gola de Pujol')
for name,g in connections:
 cross=g.intersection(unary_union([river1,river2,river3,turia]).buffer(35))
 if not cross.is_empty and g.geom_type in ['LineString','MultiLineString']:add(cross,'bridge',name='Paso de diseño · '+name)
# Compact metro/tram: station positions use OSM nodes where possible; all services are game designs.
stationlist={}
def station(code,name,ll=None,pos=None):
 p=pos if pos is not None else xy(*ll);stationlist[code]={'id':code,'name':name,'xy':p};return code
station('airport','Aeroport',pos=[terminal.centroid.x+70,terminal.centroid.y]);station('manises','Manises / Quart',pos=[-800,1500]);station('mislata','Mislata',ll=(-.417,39.475));station('cid','Av. del Cid',ll=(-.405,39.469));station('guimera','Àngel Guimerà',ll=(-.3843,39.4694));station('xativa','Xàtiva / Nord',ll=(-.3778,39.4663));station('colon','Colón',ll=(-.3703,39.4691));station('alameda','Alameda',ll=(-.3621,39.4732));station('amistat','Amistat',ll=(-.3518,39.4702));station('maritim','Marítim',ll=(-.3387,39.4628));station('neptu','Neptú / Marina',ll=(-.323,39.4615));station('facultats','Facultats · UV',ll=(-.362,39.4798));station('benimaclet','Benimaclet',ll=(-.3626,39.4853));station('alboraia','Alboraia',pos=[1450,2300]);station('empalme','Empalme',ll=(-.4071,39.4996));station('turia','Túria / Campanar',ll=(-.3907,39.4816));station('patraix','Patraix',ll=(-.3915,39.4595));station('upv','Universitat Politècnica · Vera',ll=(-.3438,39.4797));station('tarongers','Tarongers · UV',ll=(-.3384,39.4795));station('cabanyal','Cabanyal / playa',ll=(-.3277,39.4723));station('alacant','Alacant',ll=(-.378,39.4629));station('russafa','Russafa',ll=(-.3721,39.4614));station('arts','Ciutat de les Arts',ll=(-.3523,39.453));station('natzaret','Natzaret',ll=(-.3323,39.447));station('bonaire','Bonaire · estación de diseño',pos=[-2310,100]);station('cofrentes','Cofrentes · estación de diseño',pos=[-2130,-1030]);station('jalance','Jalance · estación de diseño',pos=[-2150,-2650]);station('saler','El Saler · estación de diseño',pos=[1780,-1710]);station('safor','Safor · estación de diseño',pos=[800,-3740]);station('calpe','Calpe · estación de diseño',pos=[850,-4210])
lines=[('M-A','#ffbd68',['airport','manises','mislata','cid','guimera','xativa','colon','alameda','amistat','maritim'],'metro','Corredor inspirado en L5; se omiten estaciones.'),('M-B','#f27aa2',['patraix','guimera','xativa','colon','alameda','facultats','benimaclet','alboraia'],'metro','Fusión de corredores: rama sur de diseño y eje L3/L9.'),('M-C','#a4cb6a',['empalme','turia','guimera'],'metro','Corredor inspirado en L1/L2.'),('T-U','#87d5df',['empalme','benimaclet','upv','tarongers','cabanyal','maritim'],'tram','Tranvía de diseño inspirado en L4/L6; simplifica el bucle de playas.'),('T-P','#dcb6ff',['maritim','neptu'],'tram','Enlace inspirado en L8.'),('T-S','#eeb5a0',['alacant','russafa','arts','natzaret'],'tram','Corredor inspirado en L10.'),('C-I1','#f9e365',['xativa','bonaire','cofrentes','jalance'],'regional','Cercanías de isla completamente ficticio.'),('C-I2','#ffffff',['xativa','saler','safor','calpe'],'regional','Cercanías de isla completamente ficticio.')]
transit=[];edges=[]
for id,color,st,mode,note in lines:
 pts=[stationlist[s]['xy'] for s in st];g=smooth(pts);add(g,'regional' if mode=='regional' else 'metro',name=id,color=color,mode=mode,note=note)
 transit.append({'id':id,'color':color,'stations':st,'mode':mode,'note':note,'length_m':round(g.length)})
 for a,b in zip(st,st[1:]):edges.append({'a':a,'b':b,'line':id,'length_m':round(math.dist(stationlist[a]['xy'],stationlist[b]['xy']))})
# Real interchange proximity is represented as a pedestrian transfer, never silently same station.
edges.append({'a':'xativa','b':'alacant','line':'A pie','length_m':round(math.dist(stationlist['xativa']['xy'],stationlist['alacant']['xy']))})
add(LineString([stationlist['xativa']['xy'],stationlist['alacant']['xy']]),'transfer',name='Transbordo a pie Nord–Alacant')
for s in stationlist.values():add(Point(s['xy']),'station',name=s['name'],id=s['id'])
(D/'transit.json').write_text(json.dumps({'stations':list(stationlist.values()),'lines':transit,'edges':edges},ensure_ascii=False))
# Terrain: elongated ridges and valleys. No isolated circular terrain platforms under monuments.
N=769;ext=[-4500,-5700,3800,5000];X,Y=np.meshgrid(np.linspace(ext[0],ext[2],N),np.linspace(ext[3],ext[1],N));mask=contains_xy(coast,X,Y);watermask=contains_xy(lake,X,Y)|contains_xy(portwater,X,Y)
ridge_x=-1250+360*np.sin(Y/620);ridge=520*np.exp(-((X-ridge_x)/650)**2)*np.exp(-((Y-2900)/1900)**4)
south=650*np.exp(-((Y+4200+180*np.sin(X/360))/430)**2)*np.exp(-((X+400)/1900)**4)
west=280*np.exp(-((X+3000)/600)**2)*np.exp(-((Y+1100)/2100)**4)
rock=330*np.exp(-(((X-2090)/190)**2+((Y+4470)/240)**2))
H=10+ridge+south+west+rock
for r in [river1,river2,river3]:
 # Raster valley incision along the actual designed river alignment.
 d=np.full(X.shape,1e6)
 for p in np.asarray(segmentize(r,90).coords):d=np.minimum(d,np.hypot(X-p[0],Y-p[1]))
 H*=.25+.75*np.clip(d/180,0,1)
coastdist=distance_transform_edt(mask)*((ext[2]-ext[0])/(N-1));H*=np.clip(coastdist/180,0,1)
# Flatten airfield and selected town sectors with polygonal masks, preserving ridges between them.
for m in [runway.buffer(190),terminal.buffer(100),central,*[translate(shape(s['source_mask']),s['dest'][0]-tr(*s['source'])[0],s['dest'][1]-tr(*s['source'])[1]) for s in sectors if s['zone']!='sur']]:
 inside=contains_xy(m,X,Y);blend=gaussian_filter(inside.astype(float),2);target=float(np.percentile(H[inside],20)) if inside.any() else 15;H=H*(1-blend)+target*blend
H[~mask|watermask]=0;H=np.maximum(H,0).astype('float32');np.save(D/'height.npy',H);np.save(D/'height-base.npy',H)
Image.fromarray(np.rint(H*10).astype('uint16')).save(D/'altura-decimetros.png')
cmap=LinearSegmentedColormap.from_list('isla',['#334e47','#52664d','#737759','#998c6a','#c0aa83']);rgb=LightSource(315,45).shade(H,cmap,vert_exag=1.2,dx=11,dy=14,blend_mode='soft');rgb[:,:,3]=mask.astype(float);Image.fromarray((rgb*255).astype('uint8')).save(D/'relieve.png')
(D/'terrain.json').write_text(json.dumps({'extent':ext,'size':N,'units':'height decimetres; XY metres','source':'Relieve sintético de diseño, no DEM real'}))
# Measured disjoint surface budget, with waters counted once in their containing sector.
budget={};remaining=coast
for name,m in [('Chelva y sierra norte',box(-5000,2550,1300,6000)),('Franja central: ciudad, aeropuerto e interior',box(-5000,-1000,5000,2550)),('Cofrentes y valle occidental',box(-5000,-3300,0,-1000)),('Albufera y costa',box(0,-3700,5000,-1000)),('Safor / Calpe / Ifac',box(-5000,-6000,5000,-3300))]:
 g=remaining.intersection(m);budget[name]=g.area/1e6;remaining=remaining.difference(g)
budget['Transiciones restantes']=remaining.area/1e6
for name,area in budget.items():assert area>=0
stats.update({'source_blocks':len(blocks),'retained_blocks':len(keep),'removed_blocks':len(removed)})
metrics={'island_area_km2':coast.area/1e6,'surface_budget_km2':budget,'lagoon_area_km2':lake.area/1e6,'airport_runway_m':runway.length,'airport_runway_original_m':2917.73,'f1_design_m':f1.length,'f1_reference_m':5419,'preserved_patches':len(sectors),'new_connections':len(connections),'reference_area_km2':2642.606,'retained_osm_ways':len(retainedids),**dict(stats),'road_field':diagnostics(),'notes':['The legacy 2642 km² reference excludes the later southern extension: not a valid total compression ratio.','Road topology at reconstructed seams requires engineering review.','No resident recognition study has been performed.']}
(D/'metrics-base.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));(D/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));(D/'layout.json').write_text(json.dumps({'island':mapping(coast),'area_km2':49}));(D/'landmarks-base.json').write_text(json.dumps(landmarks,ensure_ascii=False));(D/'landmarks.json').write_text(json.dumps(landmarks,ensure_ascii=False));(D/'sectors.json').write_text(json.dumps(sectors,ensure_ascii=False));(D/'seams.json').write_text(json.dumps({'source_origin_EPSG25830':origin,'block_removal_x':XS,'block_removal_y':YS,'destination_offset':OFFSET,'smooth_field':diagnostics()}))
(D/'isla-base.geojson').write_text(json.dumps({'type':'FeatureCollection','coordinate_system':'LOCAL_METRES_FICTIONAL','features':features},ensure_ascii=False,separators=(',',':')))
print(json.dumps(metrics,indent=2),flush=True);print('FEATURES',len(features),'LANDMARKS',len(landmarks),flush=True)
