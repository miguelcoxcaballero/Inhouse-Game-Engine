"""OSM snapshot extraction. Whole ways; no circular crops. Coordinates WGS84."""
import osmium,json,pathlib,unicodedata,argparse
from shapely.geometry import Polygon,LineString,Point,mapping
parser=argparse.ArgumentParser();parser.add_argument('--pbf',required=True);args=parser.parse_args()
P=pathlib.Path(__file__).resolve().parents[1];out=[];nodes=[];routes=[]
boxes=[(-.53,39.39,-.31,39.53),(-1.02,39.72,-.96,39.79),(-1.09,39.17,-1.01,39.26),(-.39,39.28,-.29,39.42),(.025,38.625,.092,38.66),(-.34,38.81,-.17,38.94)]
def inside(x,y):return any(a<x<c and b<y<d for a,b,c,d in boxes)
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
class H(osmium.SimpleHandler):
 def node(self,n):
  t=dict(n.tags)
  if inside(n.lon,n.lat) and (t.get('name') or t.get('waterway')=='waterfall') and any(k in t for k in ['amenity','place','natural','railway','tourism','waterway','historic']):nodes.append({'id':'n'+str(n.id),'tags':t,'geometry':mapping(Point(n.lon,n.lat))})
 def way(self,w):
  t=dict(w.tags)
  if not any(k in t for k in ['highway','building','waterway','railway','aeroway','landuse','leisure','natural','amenity','historic']):return
  try:c=[(n.lon,n.lat) for n in w.nodes]
  except Exception:return
  if len(c)<2 or not any(inside(*p) for p in c[::max(1,len(c)//8)]):return
  g=Polygon(c) if c[0]==c[-1] and len(c)>3 and not t.get('junction')=='roundabout' and not t.get('highway') else LineString(c)
  out.append({'id':'w'+str(w.id),'tags':t,'geometry':mapping(g)})
 def relation(self,r):
  t=dict(r.tags)
  if t.get('route') in ['subway','tram','train'] and ('metrovalencia' in norm(str(t)) or 'cercan' in norm(str(t))):routes.append({'id':r.id,'tags':t,'members':[(m.type,m.ref,m.role) for m in r.members]})
H().apply_file(args.pbf,locations=True,idx='flex_mem')
(P/'data/osm-selection.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
(P/'data/osm-nodes.json').write_text(json.dumps(nodes,ensure_ascii=False))
(P/'data/osm-transit-relations.json').write_text(json.dumps(routes,ensure_ascii=False))
print('ways',len(out),'nodes',len(nodes),'routes',len(routes))
