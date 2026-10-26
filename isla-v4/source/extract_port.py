"""Recover the full harbour from the original downloaded OSM PBF snapshot."""
from common import *
import osmium,argparse
parser=argparse.ArgumentParser();parser.add_argument('--pbf',required=True);args=parser.parse_args();out={};factory=osmium.geom.GeoJSONFactory();mask=box(*PORT_BOX)
class Handler(osmium.SimpleHandler):
 def way(self,w):
  t=dict(w.tags)
  if not any(k in t for k in ['highway','building','waterway','railway','landuse','natural','leisure']):return
  try:p=[(n.lon,n.lat) for n in w.nodes]
  except Exception:return
  if len(p)<2:return
  g=Polygon(p) if len(p)>3 and p[0]==p[-1] and not t.get('highway') else LineString(p)
  if not mask.intersects(g):return
  out['w'+str(w.id)]={'id':'w'+str(w.id),'tags':t,'geometry':mapping(g)}
 def area(self,a):
  t=dict(a.tags)
  if t.get('building:part') and not t.get('building'):return
  if not any(k in t for k in ['building','natural','landuse','leisure']):return
  try:g=json.loads(factory.create_multipolygon(a))
  except Exception:return
  if not mask.contains(shape(g).representative_point()):return
  ident=('w' if a.from_way() else 'r')+str(a.orig_id());out[ident]={'id':ident,'tags':t,'geometry':g}
Handler().apply_file(args.pbf,locations=True,idx='flex_mem');write('port-source.json.gz',list(out.values()));print('Full harbour source objects',len(out),flush=True)
