# Isla Levante · 300 km²

[Descargar el editor en ZIP](https://github.com/miguelcoxcaballero/Inhouse-Game-Engine/raw/refs/heads/main/levante-editor-300km2.zip) · [HTML del editor](isla-levante-editor-300.html) · [Visor](isla-levante-300.html)

El núcleo urbano de Valencia conserva las calles, manzanas, edificios, avenidas y distancias relativas de OSM a **escala 1:1**. No utiliza la compactación de manzanas de la versión de 100 km². Se comprueba cada huella y la geometría de las calles contra la fuente. El ámbito urbano fijo y las selecciones exteriores están definidos en `source/common.py`.

Contiene **49.859 huellas urbanas** en el ámbito fijo y **69.237 edificios** en toda la isla. Las 100 entradas arquitectónicas solicitadas se comprueban también por separado. Las calles locales conservan las coordenadas originales dentro de cada conjunto trasladado.

El aeropuerto conserva su pista completa y su disposición interna, desplazado 750 m hacia el este junto al tejido occidental. Una franja exterior a Valencia cierra esa distancia; los edificios omitidos en esa franja quedan enumerados en `data/omitted-outer-strip.json`. La Albufera, El Saler y El Palmar mantienen su geometría a tamaño real y se trasladan juntos 1,5 km hacia el norte. El embalse de Benagéber conserva una interpretación reducida de su orilla, documentada aparte.

Chelva, Cofrentes, Jalance y el sector seleccionado de Calpe se reconstruyen con sus edificios y trazados OSM dentro de ámbitos más amplios. Cada núcleo se traslada como conjunto, con sus casas enteras a tamaño real; los bordes viarios se ajustan donde hace falta integrarlos. Se incluyen el acueducto y la Playeta, la central de Cofrentes, Alboraia, Port Saplaya, Bonaire, Manises, Quart de Poblet y los pueblos del sur metropolitano. El relieve montañoso es de diseño.

En los bordes rurales se recortan caminos que se superponían a otro núcleo y se desvían los tramos que atravesaban edificios ajenos. Se omiten seis huellas periféricas por solapes con el tejido metropolitano: cinco del borde de la Albufera y una construcción rural en el extremo norte del ámbito de Cofrentes. El Saler y El Palmar conservan sus edificios. Estos cambios y los empalmes quedan enumerados en `data/regional-seams.json`; las calles del ámbito fijo de Valencia permanecen intactas.

La isla tiene **300 km²**, incluidas las aguas interiores. Su costa se ajusta por terreno exterior libre: la superficie no se obtiene escalando la ciudad. El antiguo cauce del Turia sigue siendo un parque seco, con sus puentes OSM. El nuevo cauce del sur se representa por separado; sus anchuras de diseño no constituyen un estudio hidráulico.

El contorno revisado está guardado en `data/island-outline.geojson.gz`. Redondea los bordes del terreno libre y conserva las huellas urbanas, el aeropuerto, la laguna y la costa de Valencia. La reconstrucción usa ese contorno fijo para no cambiar el mapa con cada ejecución.

## Consultar y editar

Abre el HTML del ZIP en Chrome, Edge o Firefox. Los datos y bibliotecas están incluidos. Puedes seleccionar edificios, arrastrarlos individualmente o en grupo, dibujar propuestas de calles y exportar una ficha JSON para adjuntarla al chat.

En **Escala real y conexiones**, el inspector compara las distancias entre edificios y avenidas. La capa **Conexiones verificadas** muestra recorridos por el grafo de carreteras. La malla se refiere a la base publicada; los movimientos que hagas se exportan por separado.

Las fichas de 49 o 100 km² pertenecen a otras bases y no se importan automáticamente. Esas versiones siguen disponibles en `isla-v2` e `isla-v3`.

## Comprobaciones

- `audit.json`: superficie, edificios 1:1, conservación de la ciudad, 100 elementos arquitectónicos, campus, pista y parque seco.
- `avenue-review.json`: longitudes y error geométrico respecto a las calles originales.
- `region-review.json`: edificios y calles de cada núcleo.
- `regional-seams.json`: omisiones periféricas, ajustes de caminos y comprobación de solapes entre zonas.
- `integration-review.json`: recorridos y conexiones explícitas. El grafo utiliza vértices compartidos de OSM; un cruce visual entre carreteras no crea por sí solo una intersección.
- `editor-browser-qa.json` y `viewer-browser-qa.json`: pruebas del visor, selección, arrastre, dibujo y exportación.

La comprobación vial es de conectividad sobre un grafo sin dirección. Las restricciones de giro, sentidos únicos y cotas de enlaces necesitan validación adicional antes de usarlo para navegación de vehículos. El F1 sigue siendo una interpretación sobre calles del puerto. Las alturas sin medición OSM y el relieve son aproximados.

## Reconstrucción

La fuente OSM preparada está versionada en `data/osm-source.json.gz`; la reconstrucción normal no necesita descargarla de nuevo. Se reutilizan las referencias arquitectónicas, corredores y bibliotecas versionadas de V02 y la costa de referencia de V03.

```sh
OPENBLAS_NUM_THREADS=1 python isla-v4/source/build_all.py
```

Dependencias: Python, numpy, scipy, shapely, pyproj, Pillow, matplotlib y networkx. Las pruebas de navegador utilizan Playwright y Chromium con el servidor local en el puerto 8769.

© OpenStreetMap contributors · ODbL. Las coordenadas de salida son metros de una isla ficticia y no ubicaciones geográficas reales. Procedencia y hashes: `data/provenance.json`.
