import osmium,json,pathlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--pbf',required=True);args=parser.parse_args()
P=pathlib.Path(__file__).resolve().parents[1];out=[]
refs={'A-3','A-7','V-30','V-21','V-31','V-11','CV-35','N-330','CV-500','N-332','CV-60','CV-675','CV-81','CV-31','CV-30'}
class H(osmium.SimpleHandler):
 def way(self,w):
  t=dict(w.tags)
  if t.get('highway') not in ['motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link']:return
  try:c=[(n.lon,n.lat,n.ref) for n in w.nodes]
  except:return
  if not c:return
  if not any(-1.15<x<-.26 and 39.15<y<39.82 for x,y,i in c) and not any(-.35<x<.12 and 38.60<y<38.97 for x,y,i in c):return
  if t.get('ref') not in refs and not t.get('ref','').startswith('CV-') and not t.get('highway','').endswith('_link'):return
  out.append({'id':'w'+str(w.id),'tags':t,'nodes':c})
H().apply_file(args.pbf,locations=True,idx='flex_mem')
(P/'data/corridors-osm.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')));print(len(out))
