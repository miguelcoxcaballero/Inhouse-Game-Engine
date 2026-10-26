"""Assemble a compact city from rigid, full-size OSM street blocks.
Only translations are applied to retained blocks and their buildings. Deleted
territory becomes independently routed street seams, never a scale operation.
"""
import json,math,pathlib,collections
import numpy as np
from shapely.geometry import shape,mapping,Point,Polygon,LineString,box
from shapely.affinity import translate
from shapely.ops import unary_union,nearest_points
from shapely import STRtree,make_valid
from scipy.spatial import Delaunay
from scipy.sparse.csgraph import minimum_spanning_tree

IDS=['w135630267','w23377876','w5007139','w9281502','w13073736','n12335957118','w10153012','w515256276','w12403536','w23433773','w23433774','r14693200','w23433776','w8082830','w512393709','w23455760','w23509879','w143429087','w147062296','w142736208']

def lines(g):
 if g.geom_type=='LineString' and g.length>.1:yield g
 elif hasattr(g,'geoms'):
  for p in g.geoms:yield from lines(p)

def ideal(x,y):
 # Placement targets only. Never applied to a block, building or retained street.
 from urban_backbone import position
 return position(np.asarray(x),np.asarray(y))

def build_city(D,raw,lookup,rel,coast,add,lm,stats,retainedids):
 from urban_backbone import build_backbone
 backbone=build_backbone(D,raw,rel,coast,add)
 from landmark_units import source_ensembles,emit_landmarks
 mandatory=source_ensembles(D,lookup,rel);protected_source=unary_union([u['source'] for u in mandatory])
 decisions=json.load(open(D/'block-selection-source.geojson'))['features'];blocks=[shape(f['geometry']) for f in decisions];keep=[shape(f['geometry']) for f in decisions if f['properties']['action']=='retener'];removed=[shape(f['geometry']) for f in decisions if f['properties']['action']!='retener'];tree=STRtree(keep);excluded={i for i,g in enumerate(keep) if g.intersection(protected_source).area>1};seen=set(excluded);groups=[]
 for i in range(len(keep)):
  if i in seen:continue
  todo=[i];group=[]
  while todo:
   j=todo.pop()
   if j in seen:continue
   seen.add(j);group.append(j);todo.extend(int(k) for k in tree.query(keep[j].buffer(.5),predicate='intersects') if int(k) not in seen)
  groups.append(group)
 # Split oversized ensembles along existing block boundaries; no block is cut.
 split=[]
 for group in groups:
  pending=[group]
  while pending:
   ids=pending.pop();g=unary_union([keep[i] for i in ids]);a,b,c,d=g.bounds
   if len(ids)>1 and (c-a>210 or d-b>230):
    axis=0 if c-a>d-b else 1;ids.sort(key=lambda i:keep[i].centroid.coords[0][axis]);mid=len(ids)//2;pending.extend([ids[:mid],ids[mid:]])
   else:split.append(ids)
 groups=split;owner={i:j for j,g in enumerate(groups) for i in g};units=[{'id':j,'blocks':ids,'source':unary_union([keep[i] for i in ids]),'buildings':[],'landmarks':[]} for j,ids in enumerate(groups)]
 cityrows=[]
 for o in raw:
  p=shape(o['geometry']).representative_point()
  if not(-.427<p.x<-.313 and 39.44<p.y<39.52):continue
  g=make_valid(rel(o['geometry']));cityrows.append((o,g))
  if not o['tags'].get('building') or g.geom_type not in ['Polygon','MultiPolygon']:continue
  stats['city_buildings_before']+=1;matches=tree.query(g.representative_point(),predicate='intersects')
  if len(matches) and int(matches[0]) in owner:units[owner[int(matches[0])]]['buildings'].append((o,g,int(matches[0])))
 # Landmark ensembles replace their former surrounding blocks; all their source
 # buildings stay together at real size, including unnamed buildings in a precinct.
 for u in mandatory:
  u['id']=len(units)
  for o,g in cityrows:
   if o['tags'].get('building') not in [None,'no'] and g.geom_type in ['Polygon','MultiPolygon'] and u['source'].covers(g.representative_point()):u['buildings'].append((o,g,None))
  units.append(u)
 for u in units:
  occupied=[u['source'],*[g for _,g,_ in u['buildings']]]
  occupied.extend(g for id,g in u['landmarks'] if g.geom_type in ['Polygon','MultiPolygon'] and not(lookup[id]['tags'].get('amenity')=='university' and not lookup[id]['tags'].get('building')))
  u['footprint']=unary_union(occupied);u['center']=u['source'].centroid;u['target']=np.array(ideal(u['center'].x,u['center'].y));u['reserved']=u['footprint'].buffer(7)
 constraints=json.load(open(D/'city-constraints.geojson'))['features'];hard=unary_union([shape(f['geometry']) for f in constraints if f['properties'].get('kind')!='circuit']).union(backbone.buffer(9));allowed=coast.buffer(-130).intersection(Polygon([(-100,-730),(1200,-740),(2200,-650),(2820,-300),(2780,1900),(2200,2230),(1700,2200),(1100,2360),(200,2200),(-120,1500)])).difference(hard)
 occupied=[];placement=[];omitted=list(excluded)
 # Historic core first, then larger pieces. The remaining patches retain geographic ordering.
 order=sorted(units,key=lambda u:(0 if u['landmarks'] else 1,-u['footprint'].area))
 offsets=[(0.,0.)]
 for radius in range(25,2201,25):
  for a in np.linspace(0,2*math.pi,max(12,int(radius/14)),endpoint=False):offsets.append((radius*math.cos(a),radius*math.sin(a)))
 for u in order:
  c=u['center'];local=translate(u['reserved'],-c.x,-c.y);found=None
  for dx,dy in offsets:
   if math.hypot(dx,dy)>(850 if u['landmarks'] else 700):continue
   dest=u['target']+np.array([dx,dy]);g=translate(local,*dest)
   if not allowed.covers(g) or any(g.intersects(other) for other in occupied):continue
   found=dest;occupied.append(g);break
  if found is None and not u['landmarks']:
   omitted.extend(u['blocks']);continue
  if found is None:
   (D/'packing-failure.json').write_text(json.dumps({'id':u['id'],'blocks':u['blocks'],'bounds':u['footprint'].bounds,'landmarks':[id for id,g in u['landmarks']],'source':mapping(u['source']),'footprint':mapping(u['footprint'])}))
   raise RuntimeError(f"No space for full-size block ensemble {u['id']}: {u['footprint'].area:.0f}m²; never silently scale/drop it")
  u['delta']=found-np.array(c.coords[0]);u['dest']=found;u['placed']=translate(u['source'],*u['delta']);placement.append({'id':u['id'],'blocks':u['blocks'],'source_mask':mapping(u['source']),'delta':u['delta'].tolist(),'source_centroid':list(c.coords[0]),'destination_centroid':found.tolist(),'target_displacement_m':float(np.linalg.norm(found-u['target']))})
 units=[u for u in units if 'placed' in u]
 (D/'omitted-for-avenues.json').write_text(json.dumps({'whole_blocks_omitted':omitted,'reason':'No space near original urban position after reserving main avenue/ring alignments; entire blocks removed, never shrunk.'},indent=2))
 (D/'city-packing.json').write_text(json.dumps(placement,separators=(',',':')))
 from compaction import set_packing,warp
 set_packing(placement)
 # Whole source buildings move with their blocks. No independent repacking or footprint scaling.
 bfeatures=[];building_ids=set()
 for u in units:
  for i in u['blocks']:
   src=keep[i];g=translate(src,*u['delta']);add(g,'city-block',block_id=i,ensemble=u['id'],source_area_m2=src.area,area_m2=g.area,city=True,retention='Manzana OSM íntegra: traslación, escala 1:1');bfeatures.append({'type':'Feature','geometry':mapping(g),'properties':{'block_id':i,'ensemble':u['id'],'source_area_m2':src.area,'area_m2':g.area,'perimeter_before_m':src.length,'perimeter_after_m':g.length,'delta':u['delta'].tolist()}})
  for o,g,i in u['buildings']:
   if o['id'] in building_ids:continue
   building_ids.add(o['id']);t=o['tags']
   try:h=float(t.get('height','').replace('m','')) if t.get('height') else float(t.get('building:levels',3))*3
   except:h=9
   add(translate(g,*u['delta']),'building',height=min(150,max(3,h)),name=t.get('name',''),osm=('way/' if o['id'][0]=='w' else 'relation/')+o['id'][1:],zone='valencia',city=True,rigid_block=True,block_id=i,ensemble=u['id'],source_area_m2=g.area,source='OSM · manzana íntegra, edificios y calles trasladados juntos');stats['city_buildings_after']+=1
 emit_landmarks(D,units,lookup,lm,add,building_ids)
 # All retained street curves within a patch are translated with that same patch.
 backbone_ids={f['properties']['id'] for f in json.load(open(D/'urban-backbone.geojson'))['features']}
 roadrows=[(o,g) for o,g in cityrows if o['id'] not in backbone_ids and o['tags'].get('highway') and g.geom_type in ['LineString','MultiLineString'] and o['tags']['highway'] not in ['motorway','trunk','motorway_link','trunk_link','construction','proposed']]
 roadtree=STRtree([g for o,g in roadrows]);unit_roads={};roadprops={}
 for u in units:
  mask=u['source'].buffer(9);roads=[]
  for idx in roadtree.query(mask,predicate='intersects'):
   o,g=roadrows[int(idx)];t=o['tags']
   # Stop at the real block-edge junction, not nine metres beyond it.
   for part in lines(g.intersection(u['source'])):
    ng=translate(part,*u['delta'])
    if ng.length<4:continue
    add(ng,'retained-road',name=t.get('name',''),id=o['id'],roadclass=t['highway'],bridge=t.get('bridge','no'),tunnel=t.get('tunnel','no'),city=True,ensemble=u['id'],source='OSM · manzanas íntegras; curvas y cruces trasladados 1:1');roads.append(ng);retainedids.add(o['id'])
  # Polygonized block boundaries are themselves source street centre lines.
  boundary=unary_union([keep[i].boundary for i in u['blocks']])
  for part in lines(boundary):
   ng=translate(part,*u['delta']);idx=int(roadtree.nearest(part.interpolate(.5,normalized=True)));original,source_line=roadrows[idx]
   # A plaza/polygon outline is not automatically a motor road. Preserve the
   # actual OSM class only when the boundary follows an original centre line.
   if source_line.distance(part.interpolate(.5,normalized=True))<1.5:
    t=original['tags'];add(ng,'retained-road',name=t.get('name',''),id=original['id'],roadclass=t['highway'],city=True,ensemble=u['id'],source='OSM · borde de manzana asociado a su vía original');roads.append(ng)
   else:add(ng,'block-edge',city=True,ensemble=u['id'],source='Límite de parcela o plaza; no se presupone una carretera')
  if not roads and u.get('required'):
   ng=u['placed'].buffer(3).boundary;add(ng,'new-road',name='Acceso peatonal al conjunto',roadclass='footway',city=True,source='Paseo de diseño alrededor de arquitectura protegida');roads.append(ng)
  unit_roads[u['id']]=unary_union(roads)
  # Keep parks/courtyards at full size inside the retained footprint.
  for o,g in cityrows:
   t=o['tags']
   if t.get('leisure') not in ['park','garden'] and t.get('landuse') not in ['grass','industrial']:continue
   if g.geom_type not in ['Polygon','MultiPolygon'] or not mask.covers(g):continue
   add(translate(g,*u['delta']),'industrial' if t.get('landuse')=='industrial' else 'green',name=t.get('name',''),city=True,source='OSM · espacio de manzana íntegro')
 (D/'city-blocks.geojson').write_text(json.dumps({'type':'FeatureCollection','features':bfeatures},separators=(',',':')))
 stats.update({'city_buildings_selected':len(building_ids),'city_buildings_repositioned':0,'city_building_conflicts_removed':0})
 # Build connected urban seams in the remaining space, protecting each retained block.
 from street_network import connect_city
 seam_report=connect_city(D,units,unit_roads,coast,hard,add)
 selected_keep=[g for i,g in enumerate(keep) if i not in omitted]
 report={'selected_blocks':len(selected_keep),'rigid_ensembles':len(units),'original_block_area_km2':sum(g.area for g in selected_keep)/1e6,'placed_block_area_km2':sum(f['properties']['area_m2'] for f in bfeatures)/1e6,'max_block_area_error_m2':max(abs(f['properties']['area_m2']-f['properties']['source_area_m2']) for f in bfeatures),'max_block_perimeter_error_m':max(abs(f['properties']['perimeter_after_m']-f['properties']['perimeter_before_m']) for f in bfeatures),'blocks_scaled':0,'individual_buildings_repacked':0,'urban_envelope_km2':unary_union([u['placed'] for u in units]).convex_hull.area/1e6,**seam_report,'method':'Real-size OSM blocks and buildings translated together; only streets across deleted territory are reconstructed.'}
 (D/'block-city-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(D/'manzanas-decision.geojson').write_text(json.dumps({'type':'FeatureCollection','features':decisions},separators=(',',':')))
 print('RIGID CITY',len(selected_keep),'blocks',len(units),'ensembles',stats['city_buildings_after'],'buildings',report['urban_envelope_km2'],'km2',flush=True)
 retained_index=0
 for f in decisions:
  if f['properties']['action']=='retener':
   if retained_index in omitted:f['properties']['action']='eliminar';f['properties']['reason']='Manzana completa omitida para respetar avenidas y anillos'
   retained_index+=1
 (D/'manzanas-decision.geojson').write_text(json.dumps({'type':'FeatureCollection','features':decisions},separators=(',',':')))
 return blocks,selected_keep,removed+[keep[i] for i in omitted],warp
