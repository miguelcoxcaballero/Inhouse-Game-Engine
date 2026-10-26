"""OSM Benagéber shoreline and continuous secondary-road sequences in fictional geography."""
import json,math
import numpy as np
from shapely.geometry import shape,mapping,Point,LineString
from shapely.ops import transform,nearest_points,unary_union
from shapely.affinity import affine_transform,rotate,translate
from corridor_paths import get_path,compact

def add_interior(D,fs,landmarks,coast,runway,bed,routes,tr,add,record,curve):
 raw=json.load(open(D/'benageber-osm.json'))
 original=transform(tr,shape(next(o for o in raw if o['id']=='r85608')['geometry']))
 dam_src=transform(tr,shape(next(o for o in raw if o['id']=='w227206826')['geometry']));c=dam_src.centroid
 # Rotate the dendritic shore into the freed interior. Open-water distances contract;
 # the dam itself retains its real length. Its position is a fictional design choice.
 reservoir=affine_transform(original,[0,.22,-.18,0,-2100-.22*c.y,1750+.18*c.x])
 dam=translate(rotate(dam_src,-90,origin=(c.x,c.y)),-2100-c.x,1750-c.y)
 add(reservoir,'reservoir',name='Embalse de Benagéber',osm='relation/85608',source='Contorno OSM rotado y compactado; cota de diseño 155 m')
 add(dam.buffer(8),'landmark-footprint',name='Presa de Benagéber',osm='way/227206826')
 for name,g,osm,note in [('Embalse de Benagéber',reservoir,'relation/85608','Brazos del embalse derivados de OSM. Agua compactada y girada; posición y cota ficticias.'),('Presa de Benagéber',dam,'way/227206826','Longitud de la presa OSM conservada; posición girada y trasladada al embalse de diseño.')]:
  record(name,g,'chelva',note);landmarks[-1]['osm']=osm
 # Remove obsolete connectors through the new reservoir; reconnect around its banks below.
 for f in fs:
  if f['properties']['kind'] in ['retained-road','new-road','trail','river-water']:
   g=shape(f['geometry'])
   if g.intersects(reservoir):f['geometry']=mapping(g.difference(reservoir.buffer(8)))
 # Valley outlets and access are explicit, rather than arbitrary roads crossing open water.
 outlet=curve([[-2100,1750],[-2270,1660],[-2410,1720],[-2590,1820]])
 add(outlet.buffer(11),'river-water',name='Desagüe de Benagéber · valle de diseño')
 north=[-1900,3020];summit=[-1400,3910];chelva=[-1000,2800];east=[250,3150];eastlake=[550,2250];city=[150,1500];west=[-2550,2850]
 # Each entry is a continuous real OSM route, reassembled into a compact mountain loop.
 templates={
  'CV-390':((-1.097,39.727),(-1.05,39.77)),
  'CV-395':((-.985,39.60),(-.89,39.69)),
  'CV-391':((-1.14,39.52),(-1.10,39.63)),
  'CV-25':((-.57,39.67),(-.53,39.78)),
  'CV-580':((-.78,39.17),(-.82,39.29)),
  'CV-429':((-1.05,39.38),(-.92,39.38)),
  'CV-700':((-.30,38.80),(-.17,38.83)),
  'CV-712':((-.26,38.81),(-.13,38.80)),
  'CV-755':((-.17,38.66),(-.06,38.65)),
  'CV-749':((-.03,38.68),(.01,38.72)),
  'CV-720':((-.25,38.75),(-.15,38.77))}
 specs=[
 ('CV-390','Acceso a Benagéber',[-2160,1750],[-2300,2350]),
 ('CV-391','Ladera occidental',[-2300,2350],west),
 ('CV-395','Collado occidental',west,north),
 ('CV-25','Cornisa norte',north,summit),
 ('CV-390','Chelva · enlace interior',north,chelva),
 ('CV-395','Remedio · carretera de sierra',summit,[-650,3890]),
 ('CV-25','Descenso oriental',[-650,3890],east),
 ('CV-391','Chelva · valle oriental',chelva,east),
 ('CV-390','Acceso oriental del embalse',east,eastlake),
 ('CV-395','Interior · salida hacia València',eastlake,city),
 ('CV-429','Ramal de mirador',[550,2250],[1050,2850]),
 ('CV-580','Cofrentes · ladera interior',[-2450,-700],[-1250,-1600]),
 ('CV-429','Valle de la central',[-1250,-1600],[-2180,-2630]),
 ('CV-700','Safor · collado de poniente',[-2180,-2630],[-1000,-3450]),
 ('CV-712','Safor · carretera alta',[-1000,-3450],[-450,-4150]),
 ('CV-720','Safor · ladera oriental',[-450,-4150],[600,-3600]),
 ('CV-755','Calpe · carretera de montaña',[600,-3600],[850,-4320]),
 ('CV-749','Calpe · miradores',[850,-4320],[1550,-3950]),
 ('CV-712','Valle interior · ruta secundaria',[-1250,-1600],[-600,-2800]),
 ('CV-700','Enlace de barrancos',[-600,-2800],[-1000,-3450])]
 logs=[];water=reservoir.buffer(12);forbidden=water.union(runway.buffer(100)).union(bed.buffer(5));cache={}
 for ref,name,A,B in specs:
  if ref not in cache:cache[ref]=get_path(ref,*templates[ref])
  source,ids,error=cache[ref]
  # Retain every bend of a selected source section. Choose the longest source section
  # that fits the geography without clipping water or introducing artificial straight joins.
  candidates=[];coords=list(source.coords)
  for reverse in [False,True]:
   for lo,hi in [(0,1),(0,.7),(.3,1),(.15,.85),(.25,.75)]:
    part=LineString(coords[int(lo*(len(coords)-1)):int(hi*(len(coords)-1))+1]);part=LineString(list(part.coords)[::-1]) if reverse else part
    g,m=compact(part,A,B)
    score=g.difference(coast.buffer(-15)).length*20+g.intersection(forbidden).length*50
    if not g.is_simple:score+=10000
    candidates.append((score,-part.length,g,m,part))
  score,_,g,m,part=min(candidates,key=lambda c:(c[0],c[1]))
  if score>1:raise ValueError(f'{name}: no water-safe OSM placement, penalty {score:.1f}')
  add(g,'secondary-road',name=name,ref=ref,source='Tramo continuo OSM recompuesto; ubicación de diseño',osm_ids=','.join(ids),roadclass='secondary')
  logs.append({'name':name,'ref':ref,'osm_ids':ids,'source_selection_error_m':error,'retained_source_section_m':part.length,'inside_island':coast.covers(g),'water_crossing_m':g.intersection(water).length,'runway_clearance_m':g.distance(runway),**m})
 # Short access into the existing street graph, with the main corridor given priority.
 for anchor,name in [(city,'Acceso interior a València'),([-2300,2350],'Enlace sierra / A-7'),(chelva,'Entrada de Chelva')]:
  candidates=[shape(f['geometry']) for f in fs if f['properties']['kind'] in ['retained-road','expressway','new-road'] and not shape(f['geometry']).is_empty]
  a=Point(anchor);b=nearest_points(a,unary_union(candidates))[1]
  if a.distance(b)>1:
   mid=[(a.x+b.x)/2+min(a.distance(b)*.12,25),(a.y+b.y)/2]
   g=curve([anchor,mid,list(b.coords)[0]])
   if not g.intersects(forbidden):add(g,'new-road',name=name,source='Enlace de diseño a corredor principal')
 viaduct=routes.get('CV-35',LineString()).intersection(reservoir.buffer(30))
 if not viaduct.is_empty:add(viaduct,'bridge',name='CV-35 · viaducto sobre brazo de Benagéber',source='Cruce de diseño; estructura y rasante pendientes')
 review={'source_reservoir_osm':'relation/85608','original_area_km2':original.area/1e6,'design_area_km2':reservoir.area/1e6,'dam_original_m':dam_src.length,'dam_design_m':dam.length,'reservoir_runway_clearance_m':reservoir.distance(runway),'reservoir_inside_island':coast.covers(reservoir),'cv35_reservoir_viaduct_m':viaduct.length,'secondary_routes':logs,'secondary_length_km':sum(l['design_m'] for l in logs)/1000,'chelva_coast_distance_m':Point(chelva).distance(coast.boundary),'note':'Road bends derive from real OSM sections. Positions, route combinations, terrain and reservoir level are fictional.'}
 (D/'interior-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
 return reservoir,review
