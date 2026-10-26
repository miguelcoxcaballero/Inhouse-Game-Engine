"""Valencia at actual OSM scale, complete towns, and a 300 km² island."""
from common import *
from shapely import STRtree,contains_xy,concave_hull
from shapely.affinity import scale
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter
from scipy.spatial import Delaunay
from PIL import Image
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,LinearSegmentedColormap

def main():
 raw=json.load(gzip.open(D/'osm-source.json.gz'));lookup={o['id']:o for o in raw};fs=[];records=[];landmarks=[];pois=[];road_sources=[];stats=collections.defaultdict(collections.Counter);river=[];omitted=[]
 manifest=json.load(open(OLD/'required-landmarks.json'));required={i for r in manifest for i in r['source_ids']}
 regions={key:rel(mapping(box(*r['box']))) for key,r in REGIONS.items()}
 regions['metro']=regions['metro'].difference(box(1000,-20000,20000,-6500))
 def add(g,k,**p):
  if not g.is_empty:fs.append(feature(g,k,**p))
 for index,o in enumerate(raw):
  region=region_of(o)
  if region is None:continue
  t=o['tags'];g=make_valid(rel(o['geometry']));name=t.get('name','');ident=o['id'];r=REGIONS[region];poly=g.geom_type in ['Polygon','MultiPolygon'];city=region=='metro' and g.bounds[0]>=WEST_CUT[1]
  city=region=='metro' and core_point(shape(o['geometry']).representative_point())
  props={'source_id':ident,'osm':osm(ident),'name':name,'sector':region,'zone':r['zone'],'city':city}
  if (t.get('building') not in [None,'no'] or ident in required and t.get('building:part')) and poly:
   stats[region]['source_buildings']+=1
   if region=='metro' and g.bounds[0]<WEST_CUT[1] and g.bounds[2]>WEST_CUT[0]:omitted.append(ident);continue
   delta=metro_points([g.centroid.coords[0]])[0]-g.centroid.coords[0] if region=='metro' else np.array(r['delta']);ng=translate(g,*delta);h,hs=height(t)
   airport=region=='metro' and t.get('aeroway') in ['terminal','hangar','tower']
   add(ng,'building',**props,height=h,height_source=hs,scale=1,airport=airport,ensemble=index)
   records.append({'id':ident,'sector':region,'city':city,'source':list(g.centroid.coords[0]),'destination':list(ng.centroid.coords[0]),'delta':delta.tolist(),'area_m2':g.area,'shape_error_m':0,'ensemble':index})
   stats[region]['buildings']+=1
   if name:pois.append({'id':ident,'name':name,'xy':list(ng.representative_point().coords[0]),'zone':r['zone'],'category':'OSM · edificio','osm':osm(ident),'retention':'Huella original trasladada a escala 1:1.'})
  elif t.get('highway') not in [None,'construction','proposed'] or t.get('railway') in ['rail','tram','subway','light_rail']:
   if g.geom_type not in ['LineString','MultiLineString']:continue
   cls=t.get('highway',t.get('railway'));g=g.intersection(regions[region].buffer(120))
   if region=='metro' and cls not in ['motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'] and g.bounds and g.bounds[0]>WEST_CUT[0] and g.bounds[2]<WEST_CUT[1]:continue
   kind='expressway' if cls in ['motorway','trunk','motorway_link','trunk_link'] else 'urban-arterial' if cls in ['primary','secondary','primary_link','secondary_link'] else 'retained-road'
   if not t.get('highway'):kind='railway'
   ng=move(g,region);p={**props,'roadclass':cls,'ref':t.get('ref',''),'bridge':t.get('bridge','no'),'tunnel':t.get('tunnel','no'),'layer':t.get('layer','0'),'oneway':t.get('oneway','no'),'access':t.get('access','yes')};add(ng,kind,**p);stats[region]['street_ways']+=1
   if city:road_sources.append((o,g,ng))
   if t.get('bridge') not in [None,'no']:add(ng,'bridge',**p,bridge_evidence='OSM bridge tag')
   if cls in ['footway','pedestrian','cycleway'] and any(s in name.lower() for s in ['passeig marítim','paseo marítimo','passeig de neptú']):add(ng,'promenade',**props)
  elif t.get('aeroway') in ['runway','taxiway','apron','aerodrome','stopway']:
   cls=t['aeroway'];ng=move(g,region)
   if cls=='aerodrome':add(ng,'airfield',**props)
   elif cls!='runway' or ident=='w22954021':add(ng,'airway',**props,aeroway=cls,width=float(t.get('width','45' if cls=='runway' else '18')))
  elif t.get('waterway')=='river' and ('Turia' in name or 'Túria' in name) and region=='metro':river.append(move(g.intersection(regions[region]),region))
  elif poly:
   kind=None
   if t.get('leisure') in ['park','garden']:kind='designed-park' if 'Jardí del Túria' in name else 'green'
   elif t.get('leisure') in ['pitch','playground','sports_centre']:kind='sports'
   elif t.get('natural')=='water' or t.get('landuse')=='reservoir':kind='flood-bed' if 'Nuevo Cauce' in name else 'lake' if ident=='r2786392' else 'water'
   elif t.get('natural')=='beach':kind='beach'
   elif t.get('landuse') in ['industrial','commercial','retail']:kind='industrial'
   elif t.get('landuse')=='residential':kind='urban-area'
   elif t.get('landuse') in ['farmland','orchard','allotments','plant_nursery']:kind='agriculture'
   elif t.get('natural') in ['wood','scrub'] or t.get('landuse')=='forest':kind='forest'
   elif t.get('natural') in ['bare_rock','scree']:kind='rock'
   elif t.get('natural')=='wetland':kind='wetland'
   if kind:add(move(g.intersection(regions[region]),region),kind,**props)
  elif t.get('waterway') in ['stream','river','canal']:
   g=g.intersection(regions[region]);add(move(g,region).buffer(3 if t['waterway']=='canal' else 6),'river-water',**props)
 print('SOURCE FABRIC',len(fs),'features',len(records),'buildings',dict(stats),flush=True)
 # Architectural groups follow exactly the same rigid move as their streets.
 placements=[]
 for row in manifest:
  dst=[];src=[]
  for ident in row['source_ids']:
   o=lookup[ident];g=rel(o['geometry']);region=region_of(o);ng=move(g,region);delta=np.array(ng.centroid.coords[0])-g.centroid.coords[0];h,hs=height(o['tags'])
   assert g.hausdorff_distance(translate(ng,*-delta))<1e-6,(row['name'],ident)
   add(ng,'protected-landmark',source_id=ident,scale=1,sector=region,source_area_m2=g.area,area_m2=ng.area,delta=delta.tolist());dst.append(ng);src.append(g)
   placements.append({'id':ident,'delta':delta.tolist(),'source_area_m2':g.area,'area_m2':ng.area,'height_m':h,'height_source':hs})
  g=unary_union(dst);add(g,'landmark-footprint',id=row['source_ids'][0],name=row['name']);landmarks.append({'id':row['source_ids'][0],'name':row['name'],'xy':list(g.representative_point().coords[0]),'zone':REGIONS[region]['zone'],'osm':osm(row['source_ids'][0]),'required_index':row['index'],'source_ids':row['source_ids'],'scale':1,'area_before_m2':sum(z.area for z in src),'area_after_m2':sum(z.area for z in dst),'retention':'Geometría y relaciones del conjunto OSM a tamaño real; traslación sin deformación.'})
 def place(name,ll,region='metro',ident=None):
  landmarks.append({'id':ident or 'place-'+str(len(landmarks)),'name':name,'xy':point_at(ll,region),'zone':REGIONS[region]['zone'],'retention':'Núcleo y calles OSM a escala real; emplazamiento exterior acercado a Valencia.'})
  if name=='Pinedo · playa y pueblo':landmarks[-1]['osm']='node/261004978'
 for name,ll,region in [('Alboraia · núcleo y mercado',(-.350,39.501),'metro'),('Port Saplaya · marina',(-.3205,39.5105),'metro'),('Manises · casco y cerámica',(-.463,39.492),'metro'),('Quart de Poblet · núcleo',(-.441,39.482),'metro'),('Aldaia · centro',(-.46,39.465),'metro'),('Sedaví · centro',(-.3845,39.426),'metro'),('Alfafar · centro',(-.396,39.418),'metro'),('Catarroja · centro',(-.4033,39.4033),'metro'),('Pinedo · playa y pueblo',(-.3383367,39.4217164),'metro'),('UV · campus Blasco Ibáñez',(-.3608,39.4795),'metro'),('UPV · campus de Vera',(-.3435,39.4814),'metro'),('UV · campus dels Tarongers',(-.3449,39.4768),'metro'),('Mercavalència · mercado y logística',(-.3509,39.4344),'metro'),('Chelva · iglesia de los Ángeles',(-.9969,39.7478),'chelva'),('Castillo de Cofrentes',(-1.062,39.23),'cofrentes'),('Jalance · núcleo',(-1.077,39.1915),'jalance'),('El Saler',(-.3327,39.383),'albufera'),('El Palmar',(-.3176,39.3115),'albufera'),('Calpe · casco y frente marítimo',(.0445,38.6444),'calpe'),('Penyal d’Ifac / Peñón de Ifach',(.0735,38.6346),'ifac')]:place(name,ll,region)
 for ident,name in [('r8404254','Bonaire · edificio principal'),('w126986991','Central nuclear de Cofrentes'),('w22954036','Aeropuerto · Terminal 1'),('w530977441','Aeropuerto · Terminal 2'),('w438173750','La Playeta · cascadas y remanso'),('n5858594685','Acueducto de Peña Cortada')]:
  o=lookup.get(ident) or next((n for n in json.load(gzip.open(D/'osm-nodes.json.gz')) if n['id']==ident),None)
  if o is None:raise ValueError('Missing landmark '+ident)
  g=rel(o['geometry']);region=region_of(o);ng=move(g,region);add(ng,'landmark-footprint',id=ident,name=name);landmarks.append({'id':ident,'name':name,'xy':list(ng.representative_point().coords[0]),'zone':REGIONS[region]['zone'],'osm':osm(ident),'retention':'OSM íntegro; tamaño y posición dentro de su conjunto conservados.'})
 # A full-size runway and airport grounds, on flat terrain.
 runway=next(shape(f['geometry']) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway')
 airport=unary_union([runway.buffer(170),*[shape(f['geometry']) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='apron']]).buffer(50)
 add(airport,'airfield',name='Aeropuerto de Valencia · escala real')
 # Old Turia is a park; the diverted southern floodway is separate.
 garden=unary_union([shape(f['geometry']) for f in fs if f['properties']['kind']=='designed-park'])
 axis=unary_union(river);bed=axis.buffer(95);add(axis.buffer(116),'flood-bank',name='Nuevo cauce del Turia · taludes');add(bed,'flood-bed',name='Nuevo cauce del Turia · lecho');add(axis.buffer(6).difference(garden.buffer(10)),'river-water',name='Turia · hilo de agua conceptual')
 # Generic stream/canal imports may include irrigation inside the old bed;
 # none is rendered as an active river through the dry Turia garden.
 for f in fs:
  if f['properties']['kind']=='river-water':f['geometry']=mapping(shape(f['geometry']).difference(garden.buffer(10)))
 fs[:]=[f for f in fs if not shape(f['geometry']).is_empty]
 place('Jardín del Turia · antiguo cauce, parque seco',(-.375,39.481));place('Nuevo cauce del Turia · rambla sur',(-.389,39.435))
 # Reservoir shoreline has more room than in V03, with explicit landscape scale.
 waters=json.load(open(OLD/'benageber-osm.json'));reservoir_src=rel(next(o['geometry'] for o in waters if o['id']=='r85608'));dam_src=rel(next(o['geometry'] for o in waters if o['id']=='w227206826'));anchor=dam_src.centroid
 reservoir=translate(scale(reservoir_src,.32,.32,origin=anchor),-7100-anchor.x,1000-anchor.y);dam=translate(dam_src,-7100-anchor.x,1000-anchor.y)
 add(reservoir,'reservoir',name='Embalse de Benagéber',osm='relation/85608',landscape_scale=.32);add(dam.buffer(8),'landmark-footprint',name='Presa de Benagéber')
 for name,g in [('Embalse de Benagéber',reservoir),('Presa de Benagéber',dam)]:landmarks.append({'id':'water-'+name,'name':name,'xy':list(g.representative_point().coords[0]),'zone':'chelva','retention':'Embalse reubicado y reducido; presa a tamaño real.'})
 write('building-positions.json',records);write('landmark-placement.json',placements);write('landmarks.json',landmarks);write('pois.json',pois);write('region-review.json',dict(stats));write('omitted-outer-strip.json',{'ids':omitted,'source_x_bounds':list(WEST_CUT[:2]),'closed_m':WEST_CUT[2],'scope':'Outside fixed Valencia core; airport and western nuclei move 750 m east.'})
 write('base-features.geojson.gz',fc(fs));write('regions.json',REGIONS);write('regional-layout.json',{'regions':REGIONS,'city_offset':OFFSET.tolist(),'airport_shift_m':[750,0],'albufera_shift_m':[0,1500]})
 print('FABRIC SAVED',flush=True)

if __name__=='__main__':main()
