"""Rebuild the 500 km² release from the versioned V4 baseline and neighbourhoods."""
from common import *
import subprocess,hashlib
steps=['prepare_world.py','landscape.py','connect_network.py','audit.py','build_html.py']
if '--finish' in sys.argv:steps=steps[3:]
for step in steps:
 print('BUILD',step,flush=True);subprocess.run([sys.executable,str(P/'source'/step)],check=True)
for name in ['isla-metros.geojson','building-mesh.geojson','building-avenue-relations.json']:
 (D/(name+'.gz')).write_bytes(gzip.compress((D/name).read_bytes(),compresslevel=9,mtime=0))
write('regions.json',REGIONS)
files=['island-outline.geojson.gz','valencia-neighborhoods.geojson','isla-metros.geojson.gz','building-mesh.geojson.gz','building-avenue-relations.json.gz']
write('provenance.json',{'source':'Audited V4 OSM baseline; retained footprints and city streets unchanged. Outer urban fabric removed by whole block selection.','baseline':'isla-v4/data/isla-metros.geojson.gz','baseline_sha256':hashlib.sha256((ROOT/'isla-v4/data/isla-metros.geojson.gz').read_bytes()).hexdigest(),'snapshot_utc':'2026-10-25T21:21:21Z','crs':'EPSG:25830 relative to projected (-0.377,39.4735), then fictional island translations','city_scale':1,'license':'OpenStreetMap contributors, ODbL; neighbourhoods Ajuntament de València CC BY 4.0','sha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in files}})
