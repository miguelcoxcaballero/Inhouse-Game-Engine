"""Label the main avenue once; retain source names of displaced local remnants as provenance."""
from shapely.geometry import shape
from network_review import components
from urban_backbone import GROUP

def prepare_names(features):
 for f in features:
  p=f['properties']
  if p['kind']=='retained-road' and p.get('city') and p.get('name') in GROUP:
   p['original_name']=p['name'];p['name']=''

def avenue_labels(features):
 priority=['Avinguda del Cid','Avinguda de Blasco Ibáñez','Carrer de Guillem de Castro','Gran Via de Ferran el Catòlic','Gran Via del Marqués del Túria','Avinguda de Pérez Galdós','Avinguda del Primat Reig','Avinguda del Port','Avinguda de França']
 names={f['properties'].get('name') for f in features if f['properties']['kind']=='urban-arterial'};out=[]
 for name in priority+sorted(names-set(priority)):
  rows=[f for f in features if f['properties']['kind']=='urban-arterial' and f['properties'].get('name')==name]
  if not rows or name=='Enlace urbano OSM':continue
  groups=components(rows)
  if not groups:continue
  g=groups[0]['geometry'];p=g.interpolate(.5,normalized=True);out.append({'name':name,'xy':[p.x,p.y]})
 return out
