# Isla Levante · 100 km²

[Descargar el editor en ZIP](https://github.com/miguelcoxcaballero/Inhouse-Game-Engine/raw/refs/heads/main/levante-editor-100km2.zip) · [HTML del editor](isla-levante-editor-100.html) · [Visor](isla-levante-100.html)

Abre el HTML del ZIP en un navegador. Incluye cartografía, relieve y bibliotecas; no necesita un servidor ni conexión para consultar y editar el mapa.

La isla mide **100 km²**, incluyendo aguas interiores. Esta revisión elimina **930 manzanas completas** en franjas seleccionadas y cierra el espacio que ocupaban. Se cierran 1,12 km de extensión este-oeste y 1,89 km norte-sur en las franjas seleccionadas; no es un escalado uniforme. La envolvente urbana pasa de 42,09 a 38,08 km², medida con el mismo método. Las manzanas conservadas y los conjuntos monumentales se trasladan: sus edificios mantienen las huellas OSM a tamaño real. Ciutat Vella y los núcleos de Alboraia y Port Saplaya conservan su tejido protegido.

Los giros de Blasco Ibáñez y los accesos curvos de la avenida del Cid reservan espacio propio; los tramos rectos se acortan siguiendo su dirección. El registro `block-removal-ledger.geojson.gz` distingue las manzanas suprimidas, conservadas y protegidas. `closure-strips.geojson` documenta la anchura original y la costura resultante. Se elimina también la red local que deja de servir a manzanas conservadas y se mantienen sus accesos por el grafo OSM.

La malla de referencia incluye edificios y avenidas. Una transformación continua por tramos mantiene los nodos compartidos de las calles y tiene orientación positiva. Las huellas conservadas se verifican por separado como traslaciones rígidas. Las distancias previstas del inspector corresponden a estos cortes explícitos; ya no hay un factor global del 82 %.

El **antiguo cauce del Turia es un parque seco**, con tramos, caminos, instalaciones deportivas y puentes derivados de OSM. Los estanques y fuentes ornamentales cartografiados son independientes del cauce. El nuevo cauce sur se distingue por lecho y taludes; sus anchuras son de diseño, no un levantamiento hidráulico.

## Revisar y proponer cambios

- Selecciona un edificio y arrástralo. Mayús + clic añade otros; «Recuadro» permite seleccionar varios. El movimiento de grupo conserva tamaños y distancias internas.
- Dibuja calles por puntos o a mano alzada, indica tipo, anchura y notas.
- Abre **Malla y avenidas** para activar las líneas de relación. Selecciona un edificio para comparar la distancia original, la distancia prevista tras los cortes, la distancia final y el cambio de orientación respecto a su avenida.
- Activa **Conexiones verificadas** para ver los recorridos por carretera desde Valencia hasta aeropuerto, Bonaire, Chelva, Benagéber, Cofrentes, central nuclear, El Saler, El Palmar y Calpe.
- Pulsa **Exportar ficha JSON** y adjunta el archivo en el chat. Las cifras del inspector describen la base del mapa; tus movimientos posteriores se exportan aparte.

Cada revisión cambia la base del editor, también respecto a la anterior de 100 km². Sus fichas no se mezclan automáticamente: conserva las antiguas para una migración explícita por ID OSM. La versión anterior sigue disponible en `isla-v2/`.

## Comprobaciones y límites

`data/audit.json` documenta la superficie, huellas 1:1, conjuntos protegidos, parque seco, puentes y pista del aeropuerto. `data/city-mesh-review.json` describe la malla. `data/edificios-avenidas.csv` permite revisar cada relación individual, incluidas las excepciones.

`geometry-review.json` compara las avenidas con OSM y la versión publicada anterior (`7eb26d5`; su malla se conserva en `comparison-before-mesh.npz`). `integration-review.json` comprueba nueve recorridos exteriores y enumera los componentes aún separados. Algunos fragmentos privados o secundarios siguen desconectados; la red completa no está certificada para navegación. Las restricciones de giro, carriles y cotas de puentes requieren revisión. La compactación puede omitir edificios secundarios de campus; `site-preservation-review.json` enumera los conservados y omitidos. Los 100 elementos arquitectónicos solicitados se comprueban aparte. Los avisos de lado local en curvas/extremos de segmentos necesitan revisión. El F1 es una propuesta cerrada sobre calles del puerto, no una réplica histórica. El relieve y las alturas sin dato OSM son aproximaciones.

## Datos y reconstrucción

La extracción urbana OSM, la costa de referencia y la base regional anterior se incluyen comprimidas. Las geometrías finales se distribuyen en `data/isla-metros.geojson.gz`, en metros locales de una isla ficticia. No deben interpretarse como ubicaciones geográficas reales.

Dependencias Python: numpy, scipy, shapely, pyproj, Pillow, matplotlib y networkx. Desde la raíz del repositorio:

```sh
OPENBLAS_NUM_THREADS=1 python isla-v3/source/build_all.py
```

La reconstrucción reutiliza las fuentes arquitectónicas y celdas OSM versionadas en `isla-v2/data`, además de su biblioteca MapLibre y editor. No ejecuta ni sobrescribe el generador anterior. La auditoría de navegador usa Playwright/Chromium y el servidor local 8768.

© OpenStreetMap contributors · ODbL. Referencia de barrios/distritos: Ajuntament de València, CC BY 4.0. Las fuentes, fecha de extracción y hashes están en `data/provenance.json`.
