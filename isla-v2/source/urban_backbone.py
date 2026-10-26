"""OSM primary urban structure: shorten street alignments, never scale blocks.
A common similarity of centre lines preserves all retained bends, angles and
junction relationships. Road widths are independent of this distance reduction.
"""
import json
from shapely.geometry import shape,mapping,box,LineString
from shapely.affinity import affine_transform
from shapely.ops import unary_union

FACTOR=.40
OFFSET=(1100,1100)
NAMES={
 'historic':['Carrer de Guillem de Castro','Carrer de Xàtiva','Carrer de Colón','Plaça de la Porta de la Mar','Plaça de Tetuan','Passeig de la Ciutadella','Carrer del Comte de Trénor','Carrer de la Blanqueria','Carrer del Pintor López','Plaça del Portal Nou','Plaça de Sant Agustí','Plaça del Temple'],
 'gran-via':['Gran Via de Ferran el Catòlic','Gran Via de Ramón y Cajal','Gran Via de les Germanies','Gran Via del Marqués del Túria',"Plaça d'Espanya","Plaça d'Amèrica",'Passeig de l’Albereda',"Passeig de l'Albereda"],
 'ronda':['Avinguda de Pérez Galdós','Avinguda de Giorgeta','Avinguda de Peris i Valero','Avinguda del Cardenal Benlloch','Carrer del Doctor Manuel Candela','Avinguda del Primat Reig','Avinguda Doctor Peset Aleixandre','Avinguda del General Avilés','Avinguda de Campanar','Avinguda de Pius XII','Avinguda de Burjassot','Plaça de Manuel Sanchis Guarner','Plaça de Saragossa'],
 'outer':['Ronda Nord','Ronda Nord de València','Ronda Est','Bulevar Sur','Avinguda dels Germans Machado','Avinguda de les Tres Creus','Avinguda del Doctor Tomàs Sala','Avinguda de Fernando Abril Martorell',"Avinguda d'Antonio Ferrandis (Actor)"],
 'radial':['Avinguda del Cid','Avinguda de Blasco Ibáñez','Avinguda del Port','Avinguda de França',"Avinguda d'Aragó",'Avinguda de la Constitució','Carrer de Sant Vicent Màrtir',"Avinguda d'Ausiàs March",'Avinguda de Catalunya','Avinguda de les Corts Valencianes','Avinguda dels Tarongers','Avinguda del Regne de València','Passeig de la Petxina','Carrer del General Elío','Carrer del Pla de la Saïdia','Carrer de la Trinitat','Avinguda de Menéndez Pidal','Carrer del Pla del Real','Carrer de la Serradora','Carrer del Doctor Lluch','Carrer de la Reina']}
GROUP={n:k for k,ns in NAMES.items() for n in ns}
def position(x,y):return x*FACTOR+OFFSET[0],y*FACTOR+OFFSET[1]
def build_backbone(D,raw,rel,coast,add):
 rows=[]
 for o in raw:
  t=o['tags'];g=shape(o['geometry']);c=g.representative_point();cls=t.get('highway','')
  if cls not in ['primary','secondary','tertiary','primary_link','secondary_link','tertiary_link','residential','living_street'] or g.geom_type not in ['LineString','MultiLineString']:continue
  if not(-.427<c.x<-.319 and 39.443<c.y<39.504):continue
  rows.append((o,rel(o['geometry'])))
 selected=[(o,g) for o,g in rows if o['tags'].get('name') in GROUP or o['tags'].get('bridge')=='yes' and -.405<shape(o['geometry']).centroid.x<-.35]
 graph=unary_union([g for o,g in selected]);ids={o['id'] for o,g in selected}
 # Roundabouts and short unnamed junction pieces retain the source connections.
 for o,g in rows:
  t=o['tags']
  if o['id'] not in ids and (t.get('junction')=='roundabout' or t['highway'].endswith('_link') or not t.get('name') and g.length<180) and g.distance(graph)<2:
   selected.append((o,g));ids.add(o['id'])
 out=[];source=[];summary={};M=[FACTOR,0,0,FACTOR,*OFFSET]
 # Keep major-road geometry entirely clear of the shoreline; distant extensions
 # outside the compact city terminate at the coastal street rather than in water.
 land=coast.buffer(-135)
 for o,g in selected:
  t=o['tags'];name=t.get('name','Enlace urbano OSM');ng=affine_transform(g,M).intersection(land)
  if ng.is_empty:continue
  group=GROUP.get(name,'junction');props={'kind':'urban-arterial','name':name,'roadclass':t['highway'],'id':o['id'],'osm':'way/'+o['id'][1:],'city':True,'backbone':True,'ring':group,'source':'OSM · estructura principal, giros e intersecciones conservados; distancias acortadas','alignment_length_factor':FACTOR}
  add(ng,'urban-arterial',**{k:v for k,v in props.items() if k!='kind'})
  out.append({'type':'Feature','geometry':mapping(ng),'properties':props});source.append({'type':'Feature','geometry':mapping(g),'properties':props})
  v=summary.setdefault(name,{'group':group,'source_m':0,'design_m':0,'ways':0});v['source_m']+=g.length;v['design_m']+=ng.length;v['ways']+=1
 (D/'urban-backbone.geojson').write_text(json.dumps({'type':'FeatureCollection','features':out},ensure_ascii=False,separators=(',',':')))
 (D/'urban-backbone-source.geojson').write_text(json.dumps({'type':'FeatureCollection','features':source},ensure_ascii=False,separators=(',',':')))
 (D/'urban-backbone-review.json').write_text(json.dumps({'method':'Shared similarity of source street centrelines; preserves angles, shape and common junctions. Only centreline distances shorten; blocks and buildings remain 1:1.','length_factor':FACTOR,'offset':OFFSET,'streets':summary,'selected_ways':len(out),'limitations':'These ring families are real connected street sequences, not invented circular loops. Full closed-ring traversal and grade-separated movements need review.'},ensure_ascii=False,indent=2))
 return unary_union([shape(f['geometry']) for f in out])
