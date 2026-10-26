"""Smooth, shared deformation of the selected OSM street graph.
No sinusoidal jitter, hand-drawn waviness or per-road endpoint mismatch.
The same continuous field is applied to every junction and road vertex.
Buildings use only the field at their anchor and retain their footprint.
"""
import numpy as np
from scipy.interpolate import RBFInterpolator
XS=[(-3600,-2900,50),(-2550,-1700,50),(-1400,-750,50),(-480,-320,25),(290,430,25),(650,1400,50),(2800,3550,50),(3950,4500,50)]
YS=[(-3000,-2500,50),(-1500,-1350,50),(-1150,-970,40),(-650,-350,60),(360,510,40),(800,1550,70),(2100,2900,70),(3300,3900,50)]
OFFSET=(-300,700)
def axis(a,seams):
 a=np.asarray(a,dtype=float);out=a.copy()
 for lo,hi,left in seams:out-=np.clip(a-lo,0,hi-lo)*(1-left/(hi-lo))
 return out
X0=float(axis(0,XS));Y0=float(axis(0,YS))
# Irregular control locations avoid imposing a rectangular lattice on the output.
rng=np.random.default_rng(21)
pts=np.array([(x,y) for x in np.linspace(-4200,5600,9) for y in np.linspace(-3800,5200,9)],dtype=float)
pts+=rng.uniform(-240,240,pts.shape)
target=np.column_stack((axis(pts[:,0],XS)-X0+OFFSET[0],axis(pts[:,1],YS)-Y0+OFFSET[1]))
field=RBFInterpolator(pts/1000,target/1000,kernel='thin_plate_spline',smoothing=1.8)
def warp(x,y,z=None):
 x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float);scalar=x.ndim==0
 p=np.column_stack((x.reshape(-1),y.reshape(-1)))/1000
 q=field(p)*1000
 # Urban streets close gaps after whole-block deletion; individual buildings remain unscaled.
 q[:,0]=q[:,0]*.65+800
 q[:,1]=q[:,1]*.58+500
 # Restore western neighbourhood depth; core and seafront anchors remain fixed.
 q[:,0]-=670*np.clip((850-q[:,0])/1300,0,1)
 # Move the recomposed city toward its maritime front without scaling its fabric.
 q[:,0]+=300

 if scalar:return (float(q[0,0]),float(q[0,1]))
 return q[:,0].reshape(x.shape),q[:,1].reshape(y.shape)
def diagnostics():
 X,Y=np.meshgrid(np.linspace(-3800,5300,70),np.linspace(-3400,4900,70));u,v=warp(X,Y)
 uy,ux=np.gradient(u,Y[:,0],X[0]);vy,vx=np.gradient(v,Y[:,0],X[0]);det=ux*vy-uy*vx
 return {'minimum_jacobian_determinant':float(det.min()),'positive_orientation_every_sample':bool((det>0).all()),'sample_count':int(det.size),'control_points':len(pts),'method':'Shared smooth thin-plate displacement; OSM vertices and junctions transformed together, no axis collapse'}
if __name__=='__main__':print(diagnostics())
