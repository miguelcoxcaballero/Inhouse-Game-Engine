"""Mandatory architecture is protected as complete, full-size source ensembles."""
import json
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
from shapely.affinity import translate

def source_ensembles(D,lookup,rel):
 manifest=json.load(open(D/'required-landmarks.json'));sources=json.load(open(D/'required-landmark-sources.json'))
 for o in sources:lookup[o['id']]=o
 entries=[v for v in manifest if v['index']!=96]
 for index,id,name in [(100,'w142736208','Hospital La Fe'),(101,'w23455760','Mercat Municipal del Cabanyal')]:
  entries.append({'index':index,'name':name,'source_ids':[id]})
 units=[]
 for v in entries:
  if not v['source_ids']:raise ValueError('Missing required source: '+v['name'])
  units.append({'required':[v], 'landmarks':[(id,rel(lookup[id]['geometry'])) for id in v['source_ids']]})
 # Keep recognisable landmark sequences together at their original dimensions:
 # cathedral square, market/Lonja, station/bullring and town-hall square.
 for indices in [{1,8,14,70},{0,3,21},{5,12,85},{7,18,55,59,87}]:
  selected=[u for u in units if any(v['index'] in indices for v in u['required'])]
  if len(selected)>1:
   merged={'required':[v for u in selected for v in u['required']],'landmarks':[v for u in selected for v in u['landmarks']]}
   units=[u for u in units if u not in selected]+[merged]
 # Overlapping architecture shares a translation: cathedral + Miguelete,
 # tower/church parts and compound buildings must never separate.
 changed=True
 while changed:
  changed=False
  for i,a in enumerate(units):
   ag=unary_union([g for _,g in a['landmarks']])
   for j in range(i+1,len(units)):
    bg=unary_union([g for _,g in units[j]['landmarks']])
    if ag.intersection(bg).area>.5:
     a['landmarks']+=units[j]['landmarks'];a['required']+=units[j]['required'];units.pop(j);changed=True;break
   if changed:break
 for u in units:
  u['landmarks']=list(dict(u['landmarks']).items());g=unary_union([g for _,g in u['landmarks']]);u.update({'blocks':[],'source':g.buffer(4),'buildings':[]})
 return units

def height_info(t):
 try:
  if t.get('height'):return float(t['height'].replace('m','').strip()),'OSM height'
  if t.get('building:levels'):return float(t['building:levels'])*3,'Estimate from OSM levels; not verified metres'
 except ValueError:pass
 return 9.,'Preview only; height not documented'

def emit_landmarks(D,units,lookup,lm,add,building_ids):
 placements=[]
 for u in units:
  if not u.get('required'):continue
  for id,g in u['landmarks']:
   o=lookup[id];t=o['tags'];ng=translate(g,*u['delta']);h,hs=height_info(t)
   add(ng,'protected-landmark',source_id=id,ensemble=u['id'],source_area_m2=g.area,area_m2=ng.area,scale=1,delta=u['delta'].tolist(),height=h,height_source=hs,city=True)
   if (t.get('building') not in [None,'no'] or t.get('building:part') or id=='w625039852') and id not in building_ids:
    add(ng,'building',name=t.get('name',''),osm=('way/' if id[0]=='w' else 'relation/')+id[1:],height=h,height_source=hs,source_area_m2=g.area,city=True,rigid_block=True,ensemble=u['id'],zone='valencia',source='OSM · arquitectura protegida, huella completa a escala 1:1');building_ids.add(id)
   placements.append({'id':id,'source_area_m2':g.area,'area_m2':ng.area,'delta':u['delta'].tolist(),'height_m':h,'height_source':hs})
  for v in u['required']:
   ng=unary_union([translate(dict(u['landmarks'])[id],*u['delta']) for id in v['source_ids']]);pt=ng.representative_point()
   l=lm(v['name'],pt.coords[0],id=v['source_ids'][0],g=ng,note='Huella OSM completa a escala real 1:1. El conjunto se traslada sin deformarlo. Las alturas sin dato OSM son aproximaciones de vista previa.')
   l.update({'required_index':v['index'],'source_ids':v['source_ids'],'area_before_m2':ng.area,'area_after_m2':ng.area,'scale':1,'height_status':'Consultar datos: huellas verificadas; alturas no certificadas cuando falta un valor OSM.'})
 (D/'landmark-placement.json').write_text(json.dumps(placements,ensure_ascii=False,indent=2))
