"""Moderately compact OSM airport, retaining its real orientation and internal layout."""
import json
import numpy as np
from shapely.geometry import shape,Point,LineString,mapping
from shapely.ops import unary_union
from shapely.affinity import affine_transform,translate

def build_airport(D,raw,lookup,utm,coast,add,lm):
 source=utm(lookup['w22954021']['geometry']);c=np.array(source.centroid.coords[0]);v=np.array(source.coords[-1])-source.coords[0];v/=np.linalg.norm(v)
 factor=2200/source.length;M=np.eye(2)+(factor-1)*np.outer(v,v);dest=np.array([-1950,850]);offset=dest-M@c
 matrix=[M[0,0],M[0,1],M[1,0],M[1,1],*offset]
 def move(g):return affine_transform(g,matrix)
 rows=[]
 for o in raw:
  p=shape(o['geometry']).representative_point();t=o['tags']
  if -.51<p.x<-.458 and 39.474<p.y<39.506 and t.get('aeroway') in ['runway','taxiway','apron','terminal','hangar','tower','parking_position','stopway']:rows.append((o,utm(o['geometry'])))
 grounds=[g.buffer(130) if o['tags'].get('aeroway')=='runway' else g for o,g in rows if o['tags'].get('aeroway') in ['runway','apron','terminal','hangar']]
 ground=move(unary_union(grounds).buffer(35));runway=move(source)
 add(ground,'airfield',name='Aeropuerto de València · recinto OSM recompuesto',source='OSM; se acorta el eje longitudinal, no la anchura de pista')
 count={}
 for o,g in rows:
  t=o['tags'];kind=t['aeroway'];count[kind]=count.get(kind,0)+1
  if t.get('building') or kind in ['terminal','hangar','tower']:
   pt=g.centroid;q=move(pt);ng=translate(g,q.x-pt.x,q.y-pt.y)
   add(ng,'building',name=t.get('name',''),zone='valencia',height=int(t.get('building:levels','2'))*3.5,osm='way/'+o['id'][1:],source='OSM · edificio aeroportuario entero trasladado',airport=True)
   if kind=='terminal' and o['id'] in ['w22954036','w530977441','w530977442']:
    lm('Aeropuerto · '+t.get('name','Terminal').replace('Valencia - ',''),q.coords[0],'valencia',o['id'],ng,'Terminal OSM completa, posición ajustada dentro del recinto aeroportuario recompuesto.')
  else:
   ng=move(g)
   if kind=='runway' and o['id']!='w22954021':continue
   if kind=='parking_position':continue
   add(ng,'airway',aeroway=kind,name=t.get('name',t.get('ref','')),osm='way/'+o['id'][1:],width=float(t.get('width','45' if kind=='runway' else '18')),source='Geometría OSM con compactación longitudinal moderada')
 # Terminal forecourt/service roads are selected by the actual source airport footprint.
 source_ground=unary_union(grounds).buffer(190);roadcount=0
 for o in raw:
  t=o['tags'];p=shape(o['geometry']).representative_point()
  if not(-.51<p.x<-.458 and 39.474<p.y<39.506) or t.get('highway') not in ['service','residential','unclassified','footway']:continue
  g=utm(o['geometry'])
  if not source_ground.intersects(g) or g.geom_type not in ['LineString','MultiLineString']:continue
  ng=move(g.intersection(source_ground)).difference(runway.buffer(65))
  add(ng,'retained-road',name=t.get('name','Acceso terminal'),roadclass=t['highway'],osm='way/'+o['id'][1:],source='OSM · accesos aeroportuarios recompuestos');roadcount+=1
 lm('Pista 12/30 · aeropuerto',runway.centroid.coords[0],'valencia','w22954021',runway,'Eje OSM con orientación real: 2,20 km de diseño frente a 2,918 km de geometría fuente. Anchura y posición lateral de rodajes conservadas; no certificación aeronáutica.')
 terminal=move(utm(lookup['w22954036']['geometry']))
 meta={'matrix':matrix,'runway_m':runway.length,'original_runway_m':source.length,'footprint':mapping(ground),'source_features':count,'terminal_access_ways':roadcount,'terrain_elevation_m':18,'osm_runway':'way/22954021','method':'OSM airfield with0.754 axial compaction, unchanged cross-axis distances, intact terminal/building footprints.'}
 (D/'airport-layout.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 return runway,terminal,ground
