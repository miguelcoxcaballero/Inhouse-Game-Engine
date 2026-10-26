import pathlib,zipfile,json,hashlib
P=pathlib.Path(__file__).resolve().parents[1];root=P.parent
includes=[P/'vendor/LICENSE-maplibre.txt',P/'isla-levante-v2.html',P/'README.md',P/'PROPUESTA-Y-AUDITORIA.md',*sorted((P/'research').glob('*.md')),*sorted((P/'previews').glob('*.png')),*[P/'data'/n for n in ['isla-metros.geojson','transit.json','landmarks.json','pois.json','metrics.json','audit.json','browser-qa.json','road-review.json','network-review.json','interior-review.json','beach-review.json','airport-layout.json','revision-review.json','benageber-osm.json','corridor-review.json','continuous-corridors.geojson','provenance.json','terrain.json','altura-decimetros.png','relieve.png']]]
with zipfile.ZipFile(root/'isla-levante-v2.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in includes:z.write(f,f.relative_to(root))
with zipfile.ZipFile(root/'isla-levante-v2.zip') as z:assert z.testzip() is None
manifest={'date':'2026-10-26','html_sha256':hashlib.sha256((P/'isla-levante-v2.html').read_bytes()).hexdigest(),'zip_sha256':hashlib.sha256((root/'isla-levante-v2.zip').read_bytes()).hexdigest(),'zip_bytes':(root/'isla-levante-v2.zip').stat().st_size,'scope':'Reviewable prototype; not a playable world or a claim of parity with State of Leonida.'}
(P/'data/release.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
