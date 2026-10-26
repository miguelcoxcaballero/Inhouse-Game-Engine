"""Portable viewer and feedback editor, with embedded comparison mesh."""
import pathlib,json,math,gzip,base64,re,hashlib,zipfile
import numpy as np
from PIL import Image
from shapely.geometry import shape
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data';OLD=P.parent/'isla-v2';R=6378137
def coords(c):
 if not c:return []
 if isinstance(c[0],(int,float)):return [round(c[0]/R*180/math.pi,8),round((2*math.atan(math.exp(c[1]/R))-math.pi/2)*180/math.pi,8)]
 return [coords(v) for v in c]
def geometry(g):
 if 'coordinates' in g:return {'type':g['type'],'coordinates':coords(g['coordinates'])}
 return {'type':'GeometryCollection','geometries':[geometry(v) for v in g['geometries']]}
geo=json.load(open(D/'isla-metros.geojson'))
for f in geo['features']:f['geometry']=geometry(f['geometry'])
geo.pop('coordinate_system',None)
relations=json.load(open(D/'building-avenue-relations.json'));mesh=json.load(open(D/'building-mesh.geojson'))
for f in mesh['features']:f['geometry']=geometry(f['geometry'])
for r in relations:mesh['features'].append({'type':'Feature','properties':{'kind':'avenue-relation','building':r['building'],'same_side':r['same_side']},'geometry':geometry({'type':'LineString','coordinates':[r['compact_building_xy'],r['compact_avenue_xy']]})})
routes=json.load(open(D/'integration-routes.geojson'))
for f in routes['features']:f['geometry']=geometry(f['geometry'])
import sys
sys.path.insert(0,str(OLD/'source'))
from street_labels import avenue_labels
payload={'geojson':geo,'terrain':json.load(open(D/'terrain.json')),'heights':base64.b64encode(np.asarray(Image.open(D/'altura-decimetros.png'),dtype='<u2').tobytes()).decode(),'relief':'data:image/png;base64,'+base64.b64encode((D/'relieve.png').read_bytes()).decode(),'landmarks':json.load(open(D/'landmarks.json')),'metrics':json.load(open(D/'metrics.json')),'pois':json.load(open(D/'pois.json')),'transit':json.load(open(D/'transit.json')),'urbanLabels':avenue_labels(json.load(open(D/'isla-metros.geojson'))['features']),'bounds':list(shape(json.load(open(D/'layout.json'))['island']).bounds),'relationMesh':mesh,'avenueRelations':relations,'verifiedRoutes':routes}
architecture={x['index']:x for x in json.load(open(D/'architecture-review.json'))['elements']}
for l in payload['landmarks']:
 if l.get('required_index') in architecture:l['category']='Arquitectura 1:1';l['dimension_check']=architecture[l['required_index']]
encoded=base64.b64encode(gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=9,mtime=0)).decode()
s=(OLD/'source/viewer.html').read_text().replace('V02','V04').replace('49 km²','300 km²').replace('>49<small>','>300<small>').replace('>49 <span','>300 <span')
s=s.replace('Límite: 50 km²','Superficie: 300 km²').replace('Manzanas eliminadas · isla recompuesta','Valencia a escala real · entorno acercado').replace('LEER LA COMPACTACIÓN','EXPLORAR EL MAPA')
s=s.replace('minZoom:11','minZoom:9').replace('maxBounds:[geo([-18000,-16000]),geo([18000,16000])]','maxBounds:[geo([DATA.bounds[0]-20000,DATA.bounds[1]-20000]),geo([DATA.bounds[2]+20000,DATA.bounds[3]+20000])]')
s=s.replace('<label><input id="setting-blocks"','<label hidden><input id="setting-blocks"').replace('<label><input type="checkbox" id="pieces"','<label hidden><input type="checkbox" id="pieces"')
s=s.replace("minzoom:12.8,filter:f('building')","minzoom:11.5,filter:f('building')")
s=s.replace('xy:[1350,1550]','xy:[3500,3000]').replace('xy:[-1000,3300]','xy:[-6200,7600]').replace('xy:[-2600,-2200]','xy:[-1000,-5000]').replace('xy:[1000,-2400]','xy:[6700,-10000]').replace('xy:[200,-4600]','xy:[1000,-13500]')
s=s.replace("{id:'bridges',type:'line'","{id:'railway',type:'line',source:'island',filter:['all',f('railway'),['!=',['get','roadclass'],'subway'],['!=',['get','tunnel'],'yes']],paint:{'line-color':'#7d8b87','line-width':1,'line-dasharray':[3,2]}},{id:'sports',type:'fill',source:'island',filter:f('sports'),paint:{'fill-color':'#6b9f79','fill-opacity':.85}},{id:'bridges',type:'line'")
s=s.replace("'Manzana '+(p.block_id+1)","'Conjunto '+(p.ensemble+1)")
s=s.replace("$('info-area').textContent='Original: '+Math.round(p.source_area_m2).toLocaleString('es-ES')+' m² · Isla: '+Math.round(p.area_m2).toLocaleString('es-ES')+' m².';","$('info-area').textContent='Valencia 1:1 · calles y edificios en sus posiciones relativas reales.';")
s=s.replace("DATA.metrics.removed_blocks+' de '+DATA.metrics.source_blocks+' manzanas detectadas se eliminan en el ámbito urbano; '","'Trama de Valencia a escala real, sin supresión de manzanas; '")
s=s.replace('Pista acortada, puerto y laguna reinterpretados.','Valencia y pista del aeropuerto a tamaño real. Pueblos exteriores reubicados. El antiguo cauce del Turia es un parque seco; el nuevo cauce meridional se representa por separado.')
css='''#mesh-review{position:fixed;right:16px;bottom:48px;width:290px;max-height:58vh;overflow:auto;z-index:12;padding:12px;background:#14232ff2;color:#edf0e5;border:1px solid #536b70;border-radius:9px;font:12px system-ui;box-shadow:0 8px 30px #0005}#mesh-review summary{cursor:pointer;font-weight:650;color:#bce3da}#mesh-review .mesh-controls{display:grid;gap:10px;margin-top:12px}#mesh-review label{display:flex;gap:7px}#mesh-review button{padding:8px;background:#263e45;color:#ecf2e1;border:1px solid #51666b;border-radius:5px}#mesh-review table{border-collapse:collapse;width:100%;font-size:11px}#mesh-review th{text-align:left;font-weight:400;color:#bfd0cc}#mesh-review td{text-align:right}#mesh-review td,#mesh-review th{padding:5px 0;border-bottom:1px solid #344a51}#mesh-review small,.mesh-note{font-size:10px;line-height:1.4;color:#9fb5b8}@media(max-width:640px){#mesh-review{width:230px;right:9px;bottom:42px;max-height:42vh}}'''
s=s.replace('__MAP_CSS__',(OLD/'vendor/maplibre-gl.css').read_text()).replace('__MAP_JS__',(OLD/'vendor/maplibre-gl.js').read_text().replace('</script','<\\/script')).replace('__PAYLOAD__',encoded)
s=s.replace('</head>','<style>'+css+'</style></head>').replace('</body>','<script>'+(P/'source/review-ui.js').read_text()+'</script></body>')
(P/'isla-levante-300.html').write_text(s)
digest=hashlib.sha256(encoded.encode()).hexdigest();meta={'base_id':'isla-levante-'+digest[:16],'payload_sha256':digest,'editor_version':1,'coordinate_system':'LOCAL_METRES_FICTIONAL'}
editor=s.replace('<title>Isla Levante · V04 · 300 km²</title>','<title>Levante · Editor · 300 km²</title>').replace('function showPlace(l,fly=true){if(!ready)return;','function showPlace(l,fly=true){if(!ready||window.levanteEditorActive)return;')
editor=editor.replace('</head>','<style>'+(OLD/'source/editor.css').read_text()+'</style></head>')
js=(OLD/'source/editor.js').read_text().replace('__EDITOR_META__',json.dumps(meta))
city_shapes=[shape(f['geometry']) for f in json.load(open(D/'isla-metros.geojson'))['features'] if f['properties']['kind']=='building' and f['properties'].get('city')]
city_bounds=[min(g.bounds[0] for g in city_shapes)-100,min(g.bounds[1] for g in city_shapes)-100,max(g.bounds[2] for g in city_shapes)+100,max(g.bounds[3] for g in city_shapes)+100]
js=js.replace('toMap([-100,-750]),toMap([2850,2380])','toMap('+json.dumps(city_bounds[:2])+'),toMap('+json.dumps(city_bounds[2:])+')')
js=js.replace('window.levanteEditorReady=true;',"status('Cargando las huellas de los edificios…');map.once('idle',()=>{window.levanteEditorReady=true;status('Mapa listo. Selecciona edificios o dibuja tus propuestas.');});")
editor=editor.replace('</body>',(OLD/'source/editor.html').read_text()+'<script>'+js.replace('</script','<\\/script')+'</script></body>')
(P/'isla-levante-editor-300.html').write_text(editor)
manifest={**meta,'html_sha256':hashlib.sha256(editor.encode()).hexdigest(),'html_bytes':len(editor.encode()),'viewer_bytes':len(s.encode()),'features':len(geo['features'])};(D/'editor-manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(P.parent/'levante-editor-300km2.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('Levante-editor-300km2.html',editor)
 z.writestr('LEEME.txt','Abre Levante-editor-300km2.html en Chrome, Edge o Firefox. Todos los datos están incluidos.\nSelecciona y arrastra edificios; Shift+clic añade a la selección. Dibuja propuestas y exporta el JSON para adjuntarlo en el chat.\nMalla y avenidas: activa las relaciones y pulsa un edificio para ver la comparación con OSM.\nLos JSON de versiones anteriores tienen otra base: consérvalos para una migración explícita; no se aplican automáticamente a este mapa.\n© OpenStreetMap contributors · ODbL. Relieve sintético. Prototipo en revisión.\n')
archive=P.parent/'levante-editor-300km2.zip';manifest.update({'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'zip_bytes':archive.stat().st_size,'editor_city_bounds_m':city_bounds});(D/'editor-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
