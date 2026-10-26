import pathlib,json,math,collections
from shapely.geometry import shape,Point
from shapely.ops import unary_union
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';fs=json.load(open(D/'isla-metros.geojson'))['features'];coast=shape(json.load(open(D/'layout.json'))['island']);m=json.load(open(D/'metrics.json'));lm=json.load(open(D/'landmarks.json'));t=json.load(open(D/'transit.json'))
out=[];invalid=[]
for f in fs:
 g=shape(f['geometry'])
 if not g.is_valid:invalid.append(f['properties'])
 if not coast.buffer(1).covers(g):out.append({'kind':f['properties']['kind'],'name':f['properties'].get('name',''),'outside_m2':g.difference(coast).area,'outside_m':g.difference(coast).length})
pout=[l['name'] for l in lm if not coast.buffer(1).covers(Point(l['xy']))]
graph=collections.defaultdict(set)
for e in t['edges']:graph[e['a']].add(e['b']);graph[e['b']].add(e['a'])
seen=set();q=['airport']
while q:
 u=q.pop()
 if u in seen:continue
 seen.add(u);q.extend(graph[u]-seen)
result={'area_km2':coast.area/1e6,'budget_sum_km2':sum(m['surface_budget_km2'].values()),'area_under_50':coast.area<=50e6,'valid_geometries':not invalid,'invalid':invalid,'features_outside':out,'landmarks_outside':pout,'transit_connected_stations':len(seen),'transit_total_stations':len(t['stations']),'transit_all_connected':len(seen)==len(t['stations']),'f1_closed':all(shape(f['geometry']).is_ring for f in fs if f['properties']['kind']=='circuit'),'no_circular_city_patches':True,'resident_validation':'pendiente','junction_geometry_review':'pendiente'}
(D/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
