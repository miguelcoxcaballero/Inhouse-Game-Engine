# Isla Levante · V02

**Prototipo de isla ficticia de49km², derivado de OpenStreetMap.** València y entorno, Chelva y Benagéber, Cofrentes y central, Albufera, Safor, pequeña muestra de Calpe e Ifac.

![Mapa del progreso](previews/revision-costa-chelva-cauce.png)

- [HTML interactivo autónomo](isla-levante-v2.html): abrir en un navegador actual. Incluye datos, relieve, librería de mapa, búsqueda,2D/3D, metro/tranvía compacto, Cercanías ficticio, cálculo de conexiones, modo sin rótulos, filtros de lugares, agrupación, medición, dibujo y ajustes guardados. No necesita descargar teselas ni llamar a APIs.
- [Paquete ZIP](../isla-levante-v2.zip): HTML, capturas, memoria y datos compactados.
- [Investigación e inventario anteriores al diseño](research/criterios-previos.md).
- [Propuesta, pérdidas, mediciones y auditoría](PROPUESTA-Y-AUDITORIA.md).
- [Comparación de vías rápidas con OSM](previews/vias-osm-comparacion.png).
- [Datos en metros locales](data/isla-metros.geojson), [red de transporte](data/transit.json), [auditoría geométrica](data/audit.json), [pruebas de navegador](data/browser-qa.json).

## Qué cambia

La revisión selecciona 440 de 4120 manzanas detectadas. La envolvente urbana de València es 6,75km², un 24,9 % mayor que el borrador anterior, recuperando bloques y profundidad occidental sin agrandar edificios. Mercavalència y cinco núcleos de l’Horta Sud forman la transición a huerta y marjal. Chelva pasa al interior, con Benagéber y 20 tramos secundarios/de montaña (31,7 km). Las playas están sobre la orilla. El aeropuerto recupera terminales y rodajes OSM, llanura y accesos V-11/N-220/A-3. [Control espacial](data/revision-review.json), [interior](data/interior-review.json) y [playas](data/beach-review.json).

Se retiran manzanas completas y edificios repetidos; se trasladan edificios seleccionados sin reducir sus huellas. Las curvas y cruces de la red urbana se recomponen conjuntamente con un campo continuo. Las autovías se reconstruyen desde corredores OSM continuos, contrayendo preferentemente sus rectas; se incorpora el nuevo cauce con la V-30 a ambos lados. Se ha eliminado el cierre en cuadrícula que aparecía en el primer borrador V02. El aeropuerto tiene pista de 2,20 km. Puerto, antiguo F1, laguna y relieve son interpretaciones compactadas.

**Limitaciones concretas:** no es un nivel jugable todavía. Faltan revisión de intersecciones/rasantes, conexión viaria navegable de cada acceso, fidelidad detallada del circuito histórico, ajuste del tejido urbano y validación con residentes. Metro/tranvía son servicios del juego inspirados en corredores reales; C-I1/C-I2 son inventados. No usar como información de transporte real.

La última revisión acerca València 300 m al mar, baja Chelva 200 m y la desplaza 100 m hacia el interior occidental. La CV-35 conecta directamente con el noroeste urbano; el nuevo cauce se aproxima hasta 450 m al borde sur de la ciudad, manteniendo sus extremos.

## Coordenadas y terreno

`isla-metros.geojson` usa un sistema local ficticio en metros; no debe interpretarse como EPSG:4326. El HTML los proyecta cerca del origen de Web Mercator únicamente para el visor. `altura-decimetros.png` contiene enteros de16bits,0,1m por unidad; extensión y tamaño en `terrain.json`. Altitudes diseñadas, no DEM real.

## Reproducir

Python3 con `osmium`, `shapely`, `pyproj`, `numpy`, `scipy`, `matplotlib` y `Pillow`. Los scripts no modifican el mapa real de OSM.

1. Obtener el extracto de Geofabrik de Comunitat Valenciana. La instantánea utilizada es2026-10-25T21:21:21Z; un extracto posterior puede cambiar resultados. Revisar `data/provenance.json`.
2. Ejecutar `python source/extract.py --pbf /ruta/valencia-region.osm.pbf` y `python source/extract_corridors.py --pbf /ruta/valencia-region.osm.pbf` y `python source/extract_benageber.py --pbf /ruta/valencia-region.osm.pbf`.
3. Ejecutar `OPENBLAS_NUM_THREADS=1 python source/build_model.py` y después `OPENBLAS_NUM_THREADS=1 python source/enhance_model.py`.
4. Ejecutar `python source/audit.py`, `python source/revision_audit.py`, `python source/road_review.py`, `python source/plot_corridors.py`, `python source/preview.py`, `python source/build_html.py`.
5. Servir esta carpeta por HTTP local para comprobarla en navegador. `source/qa.cjs` documenta las pruebas hechas en este entorno (requiere adaptar rutas de Chromium/Playwright si se ejecuta en otro equipo).

Los datos brutos de 89 MB y el PBF de 135 MB se excluyen de Git; las selecciones compactadas sí se entregan. `source/viewer.html` es la plantilla actual; no regenerarla desde la plantilla obsoleta V1.

## Créditos

Datos ©[OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licencia [ODbL1.0](https://opendatacommons.org/licenses/odbl/1-0/). La base derivada se ofrece bajo ODbL; conservar atribución y condiciones al redistribuirla. MapLibre GL JS5.6.2, BSD-3-Clause; licencia incluida en `vendor/`. Fuentes documentales enlazadas en la memoria; no se redistribuyen sus textos completos.

## UI y referencia visual

Se inspeccionó y descargó State of Leonida como referencia. No se encontró licencia para copiar íntegramente su código propio; esta entrega implementa una UI propia con organización y herramientas comparables. [Alcance, referencia y limitaciones](research/referencia-state-of-leonida.md). No se declara igualdad de detalle/realismo con ese proyecto.
