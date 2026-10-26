import osmium,json,pathlib,unicodedata,argparse
parser=argparse.ArgumentParser();parser.add_argument("--pbf",required=True);args=parser.parse_args()
from shapely import wkb
from shapely.geometry import mapping,Polygon,LineString,Point
P=pathlib.Path(__file__).resolve().parents[1];out=[];fac=osmium.geom.WKBFactory()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def match(t):return t.get('natural')=='water' or t.get('waterway')=='dam' or t.get('landuse')=='reservoir'
def save(id,t,g):
 c=g.representative_point()
 if -1.25<c.x<-1.02 and 39.65<c.y<39.80:out.append({'id':id,'tags':t,'geometry':mapping(g)})
class H(osmium.SimpleHandler):
 def way(self,w):
  t=dict(w.tags)
  if not match(t):return
  try:c=[(n.lon,n.lat) for n in w.nodes]
  except:return
  if len(c)>1:save('w'+str(w.id),t,Polygon(c) if c[0]==c[-1] and len(c)>3 else LineString(c))
 def area(self,a):
  t=dict(a.tags)
  if a.from_way() or not match(t):return
  try:g=wkb.loads(fac.create_multipolygon(a),hex=True)
  except:return
  save('r'+str(a.orig_id()),t,g)
H().apply_file(args.pbf,locations=True,idx='flex_mem');(P/'data/benageber-osm.json').write_text(json.dumps(out,ensure_ascii=False));print([(x['id'],x['tags'].get('name')) for x in out])
