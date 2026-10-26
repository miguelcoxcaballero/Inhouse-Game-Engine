import json,pathlib,gzip,base64,math
import numpy as np
from PIL import Image
from shapely.geometry import shape
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';R=6378137
geo=json.load(open(D/'isla-metros.geojson'))
def coords(c):
 if not c:return []
 if isinstance(c[0],(int,float)):
  x,y=c[:2];return [round(x/R*180/math.pi,8),round((2*math.atan(math.exp(y/R))-math.pi/2)*180/math.pi,8)]
 return [coords(s) for s in c]
def geometry(g):
 if 'coordinates' in g:return {'type':g['type'],'coordinates':coords(g['coordinates'])}
 return {'type':'GeometryCollection','geometries':[geometry(x) for x in g['geometries']]}
for f in geo['features']:f['geometry']=geometry(f['geometry'])
geo.pop('coordinate_system',None)
H=np.asarray(Image.open(D/'altura-decimetros.png'),dtype=float)/10;terrain=json.load(open(D/'terrain.json'));payload={'geojson':geo,'terrain':terrain,'heights':base64.b64encode(np.rint(H*10).astype('<u2').tobytes()).decode(),'relief':'data:image/png;base64,'+base64.b64encode((D/'relieve.png').read_bytes()).decode(),'landmarks':json.load(open(D/'landmarks.json')),'metrics':json.load(open(D/'metrics.json')),'pois':json.load(open(D/'pois.json')),'transit':json.load(open(D/'transit.json')),'bounds':list(shape(json.load(open(D/'layout.json'))['island']).bounds)}
compressed=base64.b64encode(gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=9)).decode()
s=(P/'source/viewer.html').read_text().replace('__MAP_CSS__',(P/'vendor/maplibre-gl.css').read_text()).replace('__MAP_JS__',(P/'vendor/maplibre-gl.js').read_text().replace('</script','<\\/script')).replace('__PAYLOAD__',compressed)
(P/'isla-levante-v2.html').write_text(s);print('BUILT',len(s)/1048576,'MiB',len(geo['features']),'features',payload['metrics']['island_area_km2'],'km2')
