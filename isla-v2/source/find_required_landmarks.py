import json,pathlib,unicodedata,re
from shapely.geometry import shape
from landmark_requirements import ITEMS
D=pathlib.Path(__file__).resolve().parents[1]/'data'
def norm(s):return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')).strip()
rows={}
for f in ['osm-nodes.json','osm-selection.json','landmark-source-areas.json']:
 for o in json.load(open(D/f)):rows[o['id']]=o
searchrows=[]
for o in rows.values():
 t=o['tags'];text=norm(' '.join(str(v) for k,v in t.items() if any(k.startswith(s) for s in ['name','official_name','alt_name','short_name','wikipedia'])))
 if text:searchrows.append((o,text))
out=[]
for i,(name,aliases) in enumerate(ITEMS):
 cs=[]
 for o,text in searchrows:
  t=o['tags']
  if not any(norm(alias) in text for alias in aliases.split('|')):continue
  g=shape(o['geometry']);pt=g.representative_point()
  if not(-.45<pt.x<-.30 and 39.28<pt.y<39.53):continue
  if t.get('highway') or t.get('route'):continue
  cs.append({'id':o['id'],'name':t.get('name'),'building':t.get('building'),'type':g.geom_type,'xy':[pt.x,pt.y],'wikidata':t.get('wikidata')})
 out.append({'index':i,'name':name,'candidates':cs})
(D/'required-landmark-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
for x in out:print(x['index'],x['name'],' :: ',[(o['id'],o['name'],o['building'],o['type']) for o in x['candidates']])
