"""Rebuild the 300 km² release from the packaged original OSM snapshot."""
from common import *
import subprocess,hashlib
steps=['build_model.py','assemble_island.py','integrate_regions.py','connect_network.py','audit.py','build_html.py']
if '--finish' in sys.argv:steps=steps[4:]
for step in steps:
 print('BUILD',step,flush=True);subprocess.run([sys.executable,str(P/'source'/step)],check=True)
for name in ['isla-metros.geojson','building-mesh.geojson','building-avenue-relations.json']:
 (D/(name+'.gz')).write_bytes(gzip.compress((D/name).read_bytes(),compresslevel=9,mtime=0))
write('regions.json',REGIONS)
files=['island-outline.geojson.gz','osm-source.json.gz','osm-nodes.json.gz','isla-metros.geojson.gz','building-mesh.geojson.gz','building-avenue-relations.json.gz']
write('provenance.json',{'source':'OpenStreetMap original project snapshot; complete urban parent footprints and source streets','snapshot_utc':'2026-10-25T21:21:21Z','crs':'EPSG:25830 relative to projected (-0.377,39.4735), then fictional island translations','city_translation_m':OFFSET.tolist(),'city_scale':1,'license':'OpenStreetMap contributors, ODbL','sha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in files}})
