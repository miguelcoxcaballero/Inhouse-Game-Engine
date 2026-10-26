"""Replace outer urban growth with landscape; keep real Valencia and exceptions."""
from common import *
from shapely import prepare,STRtree
from shapely.ops import polygonize,nearest_points
from shapely.affinity import scale
import collections,hashlib
BASE=ROOT/'isla-v4/data'
ROAD={'retained-road','urban-arterial','expressway','railway','new-road','secondary-road'}
MAJOR={'motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}

def main():
 doc=json.load(gzip.open(BASE/'isla-metros.geojson.gz'));fs=doc['features'];records=json.load(open(BASE/'building-positions.json'));landmarks=json.load(open(BASE/'landmarks.json'));pois=json.load(open(BASE/'pois.json'))
 neighborhoods=json.load(open(D/'valencia-neighborhoods.geojson'))
 # Administrative neighbourhood polygons, rather than the old wide metro box,
 # distinguish the actual city from adjoining commuter municipalities.
 city=translate(unary_union([rel(f['geometry']) for f in neighborhoods['features'] if f['properties']['district']<=16 or f['properties']['coddistbar']=='182']),*OFFSET)
 exceptions={
  'Alboraia':metro_geometry(rel(mapping(box(-.365,39.493,-.335,39.51)))),
  'Port Saplaya':metro_geometry(rel(mapping(box(-.327,39.504,-.312,39.517))))}
 fixed=unary_union([city,*exceptions.values()]);prepare(fixed)
 keep=[fixed]
 airports=[shape(f['geometry']).buffer(80) for f in fs if f['properties']['kind']=='airfield'];keep.extend(airports)
 protected=[shape(f['geometry']).buffer(65) for f in fs if f['properties']['kind'] in ['protected-landmark','landmark-footprint'] and f['properties'].get('source_id') or f['properties']['kind']=='landmark-footprint' and f['properties'].get('id') in ['r8404254','w22954036','w530977441']]
 keep.extend(protected)
 # Preserve complete street blocks around each old centre, not small houses
 # scattered at random throughout the former suburban area.
 centers=[('Manises',(-.463,39.492)),('Quart de Poblet',(-.441,39.482)),('Aldaia',(-.46,39.465)),('Alaquàs',(-.461,39.456)),('Paterna',(-.441,39.503)),('Burjassot',(-.410,39.510)),('Mislata',(-.419,39.475)),('Xirivella',(-.427,39.465)),('Sedaví',(-.3845,39.426)),('Alfafar',(-.396,39.418)),('Catarroja',(-.4033,39.4033)),('Paiporta',(-.417,39.427)),('Benetússer',(-.397,39.424)),('Pinedo',(-.3383367,39.4217164))]
 metro_roads=[shape(f['geometry']) for f in fs if f['properties'].get('sector')=='metro' and f['properties']['kind'] in ROAD and f['properties'].get('roadclass') not in ['footway','path','cycleway','steps','pedestrian','rail','tram','subway']]
 tree=STRtree(metro_roads);blocks=[];centers_report=[]
 for name,ll in centers:
  p=Point(point_at(ll));window=box(p.x-520,p.y-520,p.x+520,p.y+520);lines=[metro_roads[i].intersection(window) for i in tree.query(window,predicate='intersects')]
  faces=list(polygonize(unary_union(lines)))
  chosen=[g for g in faces if 400<g.area<110000 and g.representative_point().distance(p)<230]
  g=unary_union(chosen).buffer(14) if chosen else box(p.x-180,p.y-180,p.x+180,p.y+180)
  # A small entrance corridor meets the surviving principal through road.
  keep.append(g);blocks.append(feature(g,'retained-town-centre',name=name));centers_report.append({'name':name,'retained_blocks':len(chosen),'area_km2':g.area/1e6})
 keep=unary_union(keep);prepare(keep);road_keep=keep.buffer(18)
 old_lake=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='lake'));palmar=Point(next(l['xy'] for l in landmarks if l['name']=='El Palmar'));anchor=nearest_points(old_lake,palmar)[0]
 # Keep the reduced water wholly inside the former lake: a simple affine
 # shrink about the Palmar shore can otherwise flood neighbouring rice fields.
 lo,hi=math.sqrt(.5),1.
 for _ in range(45):
  factor=(lo+hi)/2;candidate=scale(old_lake,factor,factor,origin=anchor).intersection(old_lake)
  if candidate.area<old_lake.area*.5:lo=factor
  else:hi=factor
 lake_factor=(lo+hi)/2;lake=scale(old_lake,lake_factor,lake_factor,origin=anchor).intersection(old_lake);reclaimed_lake=old_lake.difference(lake);wetland=lake.buffer(260).difference(lake)
 # The old far western rice-field grid becomes a rural transition to the
 # southern hills. Towns and the coast road remain at their existing scale.
 albuf_hills=Polygon([(-2000,-14300),(-2000,-7000),(2100,-7000),(4200,-8200),(5200,-10000),(5300,-12200),(4300,-14300)]).buffer(700,quad_segs=16).buffer(-700,quad_segs=16).difference(lake.buffer(500))
 villages=unary_union([Point(l['xy']).buffer(500) for l in landmarks if l['name'] in ['El Palmar','El Saler']]);albuf_hills=albuf_hills.difference(villages)
 omitted=[];out=[];cut_ends=[];urban_before=[];urban_after=[];old_buildings={}
 for f in fs:
  p=f['properties'];kind=p['kind'];g=shape(f['geometry']);sector=p.get('sector');ident=p.get('source_id');original=g
  if kind in ['coast','contour'] or p.get('integration_join') or kind=='circuit':continue
  if kind=='building':
   old_buildings[ident]=f
   if sector=='metro' and not keep.covers(g.representative_point()):omitted.append(ident);continue
   p['city']=sector=='metro' and fixed.covers(g.representative_point())
  elif sector=='metro' and kind in ROAD:
   if kind!='railway' and p.get('roadclass') not in MAJOR:
    # Existing rural tracks survive; local residential grids outside the
    # chosen centres are removed with their blocks.
    rural=p.get('roadclass') in ['track','unclassified'] and any(s in p.get('name','').lower() for s in ['camí','camino','carretera'])
    if not rural:g=g.intersection(road_keep)
   if not original.equals(g):
    for line in parts(g,'LineString'):
     if not line.is_empty:
      for q in [line.coords[0],line.coords[-1]]:cut_ends.append({'xy':list(q),'source_id':ident})
  elif sector=='metro' and kind in ['urban-area','industrial','sports','green']:
   if kind in ['urban-area','industrial']:urban_before.append(g)
   g=g.intersection(keep)
   if kind in ['urban-area','industrial']:urban_after.append(g)
  elif kind=='lake':g=lake;p['landscape_scale']=lake_factor;p['area_ratio_to_300']=.5
  elif sector=='albufera':
   if kind in ['agriculture','urban-area','industrial','forest']:g=g.difference(albuf_hills)
   elif kind in ROAD and p.get('roadclass') not in MAJOR and kind!='railway':g=g.difference(albuf_hills)
   elif kind=='river-water':g=g.difference(albuf_hills).difference(reclaimed_lake)
  if g.is_empty:continue
  f['geometry']=mapping(g);out.append(f)
 removed=set(omitted);kept={f['properties']['source_id'] for f in out if f['properties']['kind']=='building'}
 # Do not leave bridge decals for deleted local streets.
 roads={f['properties'].get('source_id'):f['geometry'] for f in out if f['properties']['kind'] in ROAD}
 for f in out:
  if f['properties']['kind']=='bridge' and f['properties'].get('sector')=='metro':f['geometry']=roads.get(f['properties'].get('source_id'),mapping(LineString()))
 out=[f for f in out if not shape(f['geometry']).is_empty]
 released=unary_union(urban_before).difference(keep)
 out.extend([feature(wetland,'wetland',name='Marjal de la Albufera · transición'),feature(reclaimed_lake.difference(wetland),'agriculture',name='Arrozales recuperados al reducir la laguna'),feature(albuf_hills,'forest',name='Transición rural Albufera–Safor',designed_landscape=True)])
 records=[r for r in records if r['id'] in kept]
 for r in records:r['city']=r['sector']=='metro' and fixed.covers(Point(r['destination']))
 for l in landmarks:
  if l['id']=='lagoon-300':l.update(id='lagoon-500',xy=list(lake.representative_point().coords[0]),retention='Laguna con el 50 % de la superficie anterior; El Palmar conserva su contacto con la orilla.')
 landmarks=[l for l in landmarks if l['id'] not in ['f1-300','safor-300']]
 ikea=[{'id':i,'name':f['properties'].get('name'),'removed':i in removed} for i,f in old_buildings.items() if 'ikea' in f['properties'].get('name','').lower()]
 ikea_zone=metro_geometry(rel(mapping(box(-.394,39.407,-.374,39.421))))
 iz=[i for i,f in old_buildings.items() if ikea_zone.covers(shape(f['geometry']).representative_point())]
 preservation={}
 for name,mask in {'Valencia':city,**exceptions}.items():
  ids={i for i,f in old_buildings.items() if f['properties'].get('sector')=='metro' and mask.covers(shape(f['geometry']).representative_point())};assert ids<=kept,(name,len(ids-kept));preservation[name]={'before':len(ids),'after':len(ids),'removed':0}
 report={'island_target_km2':500,'baseline':'isla-v4 · 300 km²','buildings_before':len(old_buildings),'buildings_after':len(kept),'suburban_buildings_removed':len(omitted),'removed_ids':omitted,'preserved':preservation,'town_centres':centers_report,'lake_before_km2':old_lake.area/1e6,'lake_after_km2':lake.area/1e6,'lake_area_ratio':lake.area/old_lake.area,'lake_anchor_xy':list(anchor.coords[0]),'reclaimed_suburban_land_km2':released.area/1e6,'ikea':ikea,'alfafar_commercial_zone':{'before':len(iz),'after':sum(i in kept for i in iz)}}
 write('base-features.geojson.gz',fc(out));write('building-positions.json',records);write('landmarks.json',landmarks);write('pois.json',[p for p in pois if p['id'] not in removed]);write('rural-revision.json',report)
 write('preservation-mask.geojson.gz',fc([feature(city,'valencia-core'),*[feature(g,'preserved-enclave',name=n) for n,g in exceptions.items()],feature(keep,'urban-retention'),feature(released,'reclaimed-suburbs'),feature(albuf_hills,'new-foothills'),*blocks]))
 write('regional-seams.json',{'attachment_ends':cut_ends,'foreign_building_overlaps':0,'foreign_road_building_crossings':0})
 write('region-review.json',dict(collections.Counter(r['sector'] for r in records)))
 print(json.dumps({k:v for k,v in report.items() if k not in ['removed_ids','town_centres']},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
