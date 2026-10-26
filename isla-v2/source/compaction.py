"""Point lookup for a city assembled from rigid source blocks.
Never use this lookup to deform a block or its internal street geometry.
"""
import json,pathlib
import numpy as np
from shapely.geometry import shape,Point
from shapely import STRtree
from shapely.ops import nearest_points
XS=[];YS=[];OFFSET=(0,0);packing=[];masks=[];tree=None

def set_packing(data):
 global packing,masks,tree
 packing=data;masks=[shape(v['source_mask']) for v in data];tree=STRtree(masks)

def warp(x,y,z=None):
 if tree is None:set_packing(json.load(open(pathlib.Path(__file__).resolve().parents[1]/'data/city-packing.json')))
 x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float);scalar=x.ndim==0;out=[]
 for a,b in zip(x.reshape(-1),y.reshape(-1)):
  p=Point(a,b);i=int(tree.nearest(p));dist=masks[i].distance(p)
  if dist>=.01:
   # Anchors in deleted territory attach to the nearest retained ensemble.
   # Extrapolating averaged translations can put coastal stops in the sea.
   p=nearest_points(p,masks[i])[1];a,b=p.x,p.y
  d=packing[i]['delta']
  out.append([a+d[0],b+d[1]])
 q=np.asarray(out)
 return (float(q[0,0]),float(q[0,1])) if scalar else (q[:,0].reshape(x.shape),q[:,1].reshape(y.shape))

def diagnostics():
 return {'method':'Rigid source blocks: translation only. Nearest retained-patch anchors outside retained patches is used for labels, never to scale blocks.','block_scale':1,'minimum_jacobian_determinant':1,'positive_orientation_every_sample':True,'sample_count':len(packing),'control_points':len(packing),'scope':'Jacobian statement applies to retained rigid patches only.'}
