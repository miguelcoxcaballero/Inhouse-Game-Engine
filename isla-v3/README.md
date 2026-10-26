# Isla Levante · 100 km²

[Descargar el editor en ZIP](https://github.com/miguelcoxcaballero/Inhouse-Game-Engine/raw/refs/heads/main/levante-editor-100km2.zip) · [HTML del editor](isla-levante-editor-100.html) · [Visor](isla-levante-100.html)

Abre el HTML del ZIP en un navegador. Incluye cartografía, relieve y bibliotecas; no necesita un servidor ni conexión para consultar y editar el mapa.

Esta revisión amplía la isla de 49 a **100 km²**, incluyendo las aguas interiores. Conserva más tejido OSM de Valencia y mantiene las huellas de los edificios a tamaño real. Ciutat Vella, los conjuntos monumentales y los núcleos de Alboraia y Port Saplaya forman piezas rígidas: edificios, patios y plazas conservan sus relaciones internas.

La malla de referencia incluye los centros de todos los edificios de la extracción urbana y nodos de las avenidas. Su objetivo inicial reduce las distancias al 82 %, pero no reduce las huellas. Los conjuntos protegidos pueden ensanchar el trazado localmente; se omiten otras manzanas para hacer sitio. Una malla continua transforma las calles, sus intersecciones y los bordes de parques. Se comprueba que no tenga triángulos invertidos. Los nodos de edificios omitidos permanecen en la malla de referencia, no como edificios colocados.

El **antiguo cauce del Turia es un parque seco**, con tramos, caminos, instalaciones deportivas y puentes derivados de OSM. Los estanques y fuentes ornamentales cartografiados son independientes del cauce. El nuevo cauce sur se distingue por lecho y taludes; sus anchuras son de diseño, no un levantamiento hidráulico.

## Revisar y proponer cambios

- Selecciona un edificio y arrástralo. Mayús + clic añade otros; «Recuadro» permite seleccionar varios. El movimiento de grupo conserva tamaños y distancias internas.
- Dibuja calles por puntos o a mano alzada, indica tipo, anchura y notas.
- Abre **Malla y avenidas** para activar las líneas de relación. Selecciona un edificio para comparar la distancia original, el objetivo de compactación, la distancia final y el cambio de orientación respecto a su avenida.
- Pulsa **Exportar ficha JSON** y adjunta el archivo en el chat. Las cifras del inspector describen la base del mapa; tus movimientos posteriores se exportan aparte.

La base del editor de 100 km² es distinta de la de 49 km². Sus fichas no se mezclan automáticamente: conserva las antiguas para una migración explícita por ID OSM. La versión anterior sigue disponible en `isla-v2/`.

## Comprobaciones y límites

`data/audit.json` documenta la superficie, huellas 1:1, conjuntos protegidos, parque seco, puentes y pista del aeropuerto. `data/city-mesh-review.json` describe la malla. `data/edificios-avenidas.csv` permite revisar cada relación individual, incluidas las excepciones.

Las comprobaciones de geometría no certifican navegación, restricciones de giro, cotas de puentes ni la conectividad completa de los enlaces exteriores. Los avisos de lado local en curvas/extremos de segmentos necesitan revisión. El F1 es una propuesta cerrada sobre calles del puerto, no una réplica histórica. El relieve y las alturas sin dato OSM son aproximaciones.

## Datos y reconstrucción

La extracción urbana OSM, la costa de referencia y la base regional anterior se incluyen comprimidas. Las geometrías finales se distribuyen en `data/isla-metros.geojson.gz`, en metros locales de una isla ficticia. No deben interpretarse como ubicaciones geográficas reales.

Dependencias Python: numpy, scipy, shapely, pyproj, Pillow, matplotlib y networkx. Desde la raíz del repositorio:

```sh
OPENBLAS_NUM_THREADS=1 python isla-v3/source/build_all.py
```

La reconstrucción reutiliza las fuentes arquitectónicas y celdas OSM versionadas en `isla-v2/data`, además de su biblioteca MapLibre y editor. No ejecuta ni sobrescribe el generador anterior. La auditoría de navegador usa Playwright/Chromium y el servidor local 8768.

© OpenStreetMap contributors · ODbL. Referencia de barrios/distritos: Ajuntament de València, CC BY 4.0. Las fuentes, fecha de extracción y hashes están en `data/provenance.json`.
