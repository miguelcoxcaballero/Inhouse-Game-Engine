"""Keep the interpreted harbour circuit closed and outside protected architecture."""
import json,numpy as np
from shapely.geometry import shape,mapping,Point,LineString
from shapely.ops import unary_union
from street_network import GroundRouter

def recompose_circuit(D,fs,coast,landmarks):
 f=next(f for f in fs if f['properties']['kind']=='circuit');g=shape(f['geometry'])
 obstacles=unary_union([shape(x['geometry']).buffer(9) for x in fs if x['properties']['kind'] in ['protected-landmark','building','water']])
 router=GroundRouter((1000,-1500,3400,1600),obstacles,coast.buffer(-15),5)
 from scipy.ndimage import label
 labels,count=label(router.free);sizes=np.bincount(labels.ravel());sizes[0]=0;router.free=labels==int(sizes.argmax())
 def accessible(p):return router.valid(LineString([p,Point(p.x+.001,p.y)])) and router.index(p) is not None
 pts=[g.interpolate(s) for s in np.arange(0,g.length,12)];valid=[accessible(p) for p in pts]
 start=valid.index(True);pts=pts[start:]+pts[:start];pts.append(pts[0]);out=[pts[0].coords[0]];i=0;changed=0
 while i<len(pts)-1:
  direct=LineString([pts[i],pts[i+1]])
  if router.valid(direct) and accessible(pts[i+1]):out.append(pts[i+1].coords[0]);i+=1;continue
  j=i+1
  while j<len(pts)-1 and not accessible(pts[j]):j+=1
  replacement=router.route(pts[i],pts[j])
  if replacement is None:raise RuntimeError('Circuit cannot avoid protected buildings at retained route seam')
  out.extend(list(replacement.coords)[1:]);i=j;changed+=1
 result=LineString(out)
 assert result.is_ring and not result.intersects(obstacles)
 f['geometry']=mapping(result);f['properties']['source']='Interpretación compacta del circuito; costuras ajustadas alrededor de arquitectura 1:1; fidelidad histórica pendiente'
 for l in landmarks:
  if 'circuito de Fórmula' in l['name']:l['xy']=list(result.interpolate(.15,normalized=True).coords[0])
 (D/'circuit-review.json').write_text(json.dumps({'closed':True,'protected_footprint_crossing_m':0,'reconstructed_sections':changed,'length_m':result.length,'historical_fidelity':'Pending; interpreted loop, not a survey of the original course.'},indent=2))
 return result.length
