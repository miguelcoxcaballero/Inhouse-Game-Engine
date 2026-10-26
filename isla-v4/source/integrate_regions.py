"""Resolve overlaps at relocated rural edges without changing fixed Valencia."""
from common import *
from shapely import STRtree,prepare,line_merge
from shapely.geometry import MultiLineString
sys.path.insert(0,str(ROOT/'isla-v2/source'))
from street_network import GroundRouter
ROAD={'retained-road','urban-arterial','expressway','railway'}

def main():
 doc=json.load(open(D/'isla-metros.geojson'));fs=[f for f in doc['features'] if not f['properties'].get('integration_join') and f['properties']['kind']!='circuit']
 coast=shape(next(f['geometry'] for f in fs if f['properties']['kind']=='coast'));land=coast.buffer(-1);prepare(land)
 core=translate(unary_union([rel(mapping(box(*b))) for b in [CITY_BOX,PORT_BOX]]),*OFFSET);outer_land=land.difference(core);prepare(outer_land)
 buildings=[f for f in fs if f['properties']['kind']=='building'];geoms=[shape(f['geometry']) for f in buildings];tree=STRtree(geoms);omitted=set()
 # The fixed city's streets take priority over a relocated rural outbuilding
 # whose footprint just intrudes across the settlement boundary.
 border=[i for i,(f,g) in enumerate(zip(buildings,geoms)) if f['properties']['sector']!='metro' and g.intersects(core)]
 if border:
  border_tree=STRtree([geoms[i] for i in border])
  for f in fs:
   if f['properties'].get('sector')!='metro' or f['properties']['kind'] not in ROAD:continue
   g=shape(f['geometry'])
   for j in border_tree.query(g,predicate='intersects'):
    i=border[j]
    if g.intersection(geoms[i]).intersection(core).length>.01:omitted.add(buildings[i]['properties']['source_id'])
 for i,g in enumerate(geoms):
  for j in tree.query(g,predicate='intersects'):
   if j<=i or buildings[i]['properties']['sector']==buildings[j]['properties']['sector'] or g.intersection(geoms[j]).area<1:continue
   pair=[buildings[i],buildings[j]];candidate=next((f for f in pair if f['properties']['sector']=='albufera' and shape(f['geometry']).centroid.y>-5800),None)
   assert candidate is not None,('Unresolved settlement overlap',[f['properties']['source_id'] for f in pair])
   omitted.add(candidate['properties']['source_id'])
 fs=[f for f in fs if not (f['properties']['kind']=='building' and f['properties']['source_id'] in omitted)]
 buildings=[f for f in fs if f['properties']['kind']=='building'];geoms=[shape(f['geometry']) for f in buildings];tree=STRtree(geoms)
 hard=unary_union([g.buffer(1.5) for g in geoms]+[shape(f['geometry']).buffer(1) for f in fs if f['properties']['kind'] in ['lake','reservoir','water','flood-bed']]+[shape(f['geometry']).buffer(95) for f in fs if f['properties']['kind']=='airway' and f['properties'].get('aeroway')=='runway']);prepare(hard)
 calpe=unary_union([g for f,g in zip(buildings,geoms) if f['properties']['sector']=='calpe']).convex_hull.buffer(80)
 outer_field_mask=unary_union([box(-18000,-5800,6000,15000),calpe]);adjusted=[];ends=[];clipped=[]
 def route(a,b,metro=False):
  for step,margin in [(6,180),(4,450)]:
   bounds=(min(a[0],b[0])-margin,min(a[1],b[1])-margin,max(a[0],b[0])+margin,max(a[1],b[1])+margin)
   router=GroundRouter(bounds,hard,outer_land if metro else land,step);g=router.route(Point(a),Point(b))
   if g is None:continue
   p=np.array(g.coords)
   for _ in range(3):
    q=[p[0]]
    for u,v in zip(p,p[1:]):q.extend([u*.75+v*.25,u*.25+v*.75])
    q.append(p[-1]);ng=LineString(q)
    if not router.valid(ng):break
    p=np.array(q)
   return LineString(p)
  return None
 updated={}
 for f in fs:
  p=f['properties'];kind=p['kind'];sector=p.get('sector')
  if kind not in ROAD:continue
  original=shape(f['geometry']);g=original
  original_ends=[Point(q) for line in parts(original,'LineString') if not line.is_empty for q in [line.coords[0],line.coords[-1]]]
  def new_end(q):return all(Point(q).distance(p)>.02 for p in original_ends)
  if sector=='albufera':
   g=g.difference(outer_field_mask)
   if original.length-g.length>.01:clipped.append(p['source_id'])
  foreign=[geoms[j].buffer(8) for j in tree.query(g,predicate='intersects') if buildings[j]['properties']['sector']!=sector]
  if foreign:
   cut=unary_union(foreign);result=[];reroutes=0
   if sector=='metro':cut=cut.difference(core)
   for source_line in parts(g,'LineString'):
    pieces=sorted((z for z in parts(source_line.difference(cut),'LineString') if not z.is_empty),key=lambda z:source_line.project(Point(z.coords[0])))
    result.extend(pieces)
    for a,b in zip(pieces,pieces[1:]):
     u,v=a.coords[-1],b.coords[0];new=route(u,v,sector=='metro')
     if new is not None:result.append(new);reroutes+=1
    for line in pieces:
     for q in [line.coords[0],line.coords[-1]]:
      if new_end(q):ends.append({'xy':list(q),'source_id':p['source_id']})
   g=line_merge(MultiLineString(result)) if result else LineString();adjusted.append({'id':p['source_id'],'sector':sector,'routed_gaps':reroutes,'source_length_m':original.length,'final_length_m':g.length});p['seam_adjusted']=True
  if g.is_empty or original.hausdorff_distance(g)>.001:
   p['outer_edge_processed']=True;updated[p['source_id']]=g
   for line in parts(g,'LineString'):
    if line.is_empty:continue
    for q in [line.coords[0],line.coords[-1]]:
     if new_end(q):ends.append({'xy':list(q),'source_id':p['source_id']})
  f['geometry']=mapping(g)
  if len(adjusted) and len(adjusted)%20==0 and foreign:print('EDGE ROADS',len(adjusted),flush=True)
 # Bridge overlays must describe the same final geometry as their source way.
 for f in fs:
  p=f['properties']
  if p['kind']=='bridge' and p.get('source_id') in updated:f['geometry']=mapping(updated[p['source_id']])
 fs=[f for f in fs if not shape(f['geometry']).is_empty]
 # Assert that the recomposition has introduced no road through a foreign house.
 remaining=[]
 for f in fs:
  p=f['properties']
  if p['kind'] not in ROAD:continue
  g=shape(f['geometry'])
  for j in tree.query(g,predicate='intersects'):
   if buildings[j]['properties']['sector']!=p.get('sector') and g.intersection(geoms[j].buffer(-.05)).length>.01:remaining.append((p.get('source_id'),buildings[j]['properties']['source_id']))
 assert not remaining,remaining[:10]
 records_before=json.load(open(D/'building-positions.json'));records=[r for r in records_before if r['id'] not in omitted];stats=json.load(open(D/'region-review.json'))
 for sector in REGIONS:
  count=sum(r['id'] in omitted and r['sector']==sector for r in records_before)
  if count:stats[sector]['buildings']-=count;stats[sector]['outer_edge_omissions']=count
 metrics=json.load(open(D/'metrics.json'));metrics['total_buildings']=len(records);metrics.pop('integration',None);metrics.pop('source_blocks',None)
 doc['features']=fs;write('isla-metros.geojson',doc);write('building-positions.json',records);write('region-review.json',stats);write('metrics.json',metrics)
 write('regional-seams.json',{'omitted_outer_buildings':sorted(omitted),'reason':'Relocated northern agricultural edge overlaps the fixed metropolitan fabric; El Saler, El Palmar and all fixed city buildings remain intact.','adjusted_road_ways':adjusted,'field_road_ways_clipped':sorted(set(clipped)),'attachment_ends':ends,'foreign_building_overlaps':0,'foreign_road_building_crossings':0})
 print('REGIONAL EDGES',len(omitted),'peripheral footprints omitted;',len(adjusted),'road ways adjusted;',len(set(clipped)),'field-road ways clipped',flush=True)

if __name__=='__main__':main()
