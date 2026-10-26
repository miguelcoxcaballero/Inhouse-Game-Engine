# Isla Levante · 500 km²

[Descargar el editor en ZIP](https://github.com/miguelcoxcaballero/Inhouse-Game-Engine/raw/refs/heads/main/levante-editor-500km2.zip) · [HTML del editor](isla-levante-editor-500.html) · [Visor](isla-levante-500.html) · [Captura](previews/isla-500.png)

La isla amplía su superficie de 300 a **500 km²**, incluidas las aguas interiores. Los 200 km² nuevos se añaden principalmente al interior. Se sustituyen grandes extensiones suburbanas por campo y sierras, conservando Valencia a escala real, Alboraia y Port Saplaya.

Se eliminan **25.499 huellas suburbanas** de la base anterior. En los pueblos metropolitanos se seleccionan manzanas completas alrededor de sus centros históricos; los edificios retenidos conservan sus huellas y coordenadas. La zona comercial e industrial de Alfafar donde está IKEA pasa de 1.175 a 6 huellas dentro del ámbito seleccionado. Bonaire y el aeropuerto se conservan.

Valencia se distingue de sus municipios vecinos mediante sus barrios oficiales: distritos 1–16 y Beniferri. Se conservan las **31.156 huellas** de ese ámbito, las **969 de Alboraia** y las **175 de Port Saplaya**; algunos límites de selección se solapan. La isla contiene **43.738 edificios**. Esta clasificación es más precisa que el gran recuadro metropolitano de V4, por lo que sus cifras de «edificios urbanos» no son directamente comparables.

La laguna de la Albufera pasa de **24,31 a 12,15 km²**, conservando su contorno reconocible y anclando la reducción en la orilla más próxima a El Palmar. El Saler y El Palmar mantienen sus edificios a tamaño real. La nueva lámina de agua queda íntegramente dentro de la antigua para no inundar construcciones. La superficie recuperada de la laguna se convierte en arrozales y marjal. El antiguo cauce del Turia sigue siendo un parque seco, con sus puentes; el nuevo cauce meridional se representa por separado.

El aeropuerto mantiene su pista de **2,92 km**, sus edificios y el desplazamiento previo de 750 m hacia Valencia. El terreno del recinto y de sus inmediaciones permanece llano. Los 100 elementos arquitectónicos protegidos mantienen las huellas 1:1 de la base auditada.

Las nuevas carreteras secundarias forman recorridos por las sierras occidentales y del sur. Se ajustan perfiles de curvas procedentes de OSM a los cruces de la isla y se comprueba que los enlaces nuevos evitan edificios, agua y la pista. Son trazados de diseño: no representan carreteras reales en sus posiciones geográficas originales ni un proyecto de rasantes.

## Usar y exportar sugerencias

Descomprime el ZIP y abre el HTML en Chrome, Edge o Firefox. Todos los datos y bibliotecas están incluidos. GitHub muestra el HTML como código; utiliza el enlace de descarga del ZIP.

Puedes dibujar calles por puntos o a mano alzada, seleccionar edificios con Shift o con un rectángulo, moverlos en grupo y exportar la ficha JSON para adjuntarla al chat. La malla y el inspector de avenidas permiten consultar las relaciones espaciales de la base. Los movimientos manuales se guardan por separado.

Los JSON de versiones anteriores tienen otro identificador de base y requieren migración explícita; el editor evita aplicarlos al mapa equivocado. Las versiones de 300, 100 y 49 km² permanecen disponibles.

## Datos y comprobaciones

- [Auditoría geométrica](data/audit.json): edificios y calles preservados frente a V4, superficie, arquitectura, pista, cauce seco y reducción suburbana.
- [Revisión rural](data/rural-revision.json): edificios omitidos, manzanas de pueblos seleccionadas y superficies antes/después.
- [Conectividad](data/integration-review.json): 18 destinos comprobados sobre vértices compartidos y empalmes explícitos.
- [Carreteras de montaña](data/scenic-road-review.json): trazados y longitudes de los recorridos nuevos.
- [Paisaje](data/landscape-review.json): superficie añadida, campos recuperados y monte de diseño.
- [Prueba del visor](data/viewer-browser-qa.json), [prueba del editor](data/editor-browser-qa.json) e [inspector](data/inspector-editor-qa.json).

La conectividad utiliza un grafo sin dirección; un cruce visual entre puentes no crea una intersección. Sentidos únicos, giros y cotas necesitan desarrollo para navegación de vehículos. El relieve es sintético; las alturas sin medición OSM son vistas previas. El antiguo circuito de F1 sigue siendo una interpretación sobre calles del puerto.

## Reproducir

```sh
OPENBLAS_NUM_THREADS=1 python isla-v5/source/build_all.py
```

Dependencias: Python, numpy, scipy, shapely, pyproj, Pillow, matplotlib y networkx. La reconstrucción usa la base OSM auditada y versionada de `isla-v4`, los corredores y bibliotecas de `isla-v2` y los barrios incluidos en esta carpeta. Las pruebas de navegador usan Playwright/Chromium y un servidor local en el puerto 8770.

© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL. Barrios: [Ajuntament de València](https://opendata.vlci.valencia.es/dataset/barris-barrios), CC BY 4.0. MapLibre GL JS, BSD-3-Clause. Coordenadas en metros de una isla ficticia. [Procedencia y hashes](data/provenance.json).
