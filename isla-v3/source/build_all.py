"""Rebuild the self-contained 100 km² release, without changing V02."""
import pathlib,subprocess,sys,gzip,json,hashlib
P=pathlib.Path(__file__).resolve().parents[1];D=P/'data'
steps=['mesh_city.py','build_world.py','integrate_routes.py','geometry_review.py','audit.py','build_html.py']
if '--world-only' in sys.argv:steps=steps[1:]
for name in steps:
 print('BUILD',name,flush=True);subprocess.run([sys.executable,str(P/'source'/name)],check=True)
for name in ['isla-metros.geojson','city-features.geojson','building-mesh.geojson','building-avenue-relations.json']:
 f=D/name;(D/(name+'.gz')).write_bytes(gzip.compress(f.read_bytes(),compresslevel=9,mtime=0))
files=['osm-urban-source.json.gz','source-coast.geojson.gz','baseline-49.json.gz','comparison-before-mesh.npz','block-removal-ledger.geojson.gz','isla-metros.geojson.gz','displacement-mesh.npz','guidance-mesh.npz']
(D/'provenance.json').write_text(json.dumps({'source':'OpenStreetMap, original project extraction','osm_snapshot_utc':'2026-10-25T21:21:21Z','baseline_commit':'8b3b342702b3ef4b94c4dd55bfad1146d818b3cd','coordinate_system':'EPSG:25830 metres relative to projected (-0.377,39.4735); output is fictional local metres','license':'OpenStreetMap contributors, ODbL','sha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in files}},indent=2))
