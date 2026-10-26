"""Full OSM areas, including multipolygon buildings omitted by way-only extraction."""
import json,pathlib,osmium,argparse
parser=argparse.ArgumentParser();parser.add_argument("--pbf",required=True);args=parser.parse_args()
from shapely.geometry import shape
P=pathlib.Path(__file__).resolve().parents[1];factory=osmium.geom.GeoJSONFactory();out=[]
class H(osmium.SimpleHandler):
 def area(self,a):
  t=dict(a.tags)
  if not any(k in t for k in ['name','name:es','name:ca','building','building:part']):return
  try:g=json.loads(factory.create_multipolygon(a));c=shape(g).representative_point()
  except Exception:return
  if not(-.45<c.x<-.30 and 39.28<c.y<39.53):return
  out.append({'id':('w' if a.from_way() else 'r')+str(a.orig_id()),'tags':t,'geometry':g})
H().apply_file(args.pbf,locations=True,idx='flex_mem')
(P/'data/landmark-source-areas.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')));print('Full areas',len(out))
