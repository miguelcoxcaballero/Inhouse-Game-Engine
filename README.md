# Inhouse-Game-Engine

Atlas interactivo con cartografía real de OpenStreetMap y una estética inspirada en GTA VI.

## Descargar y abrir

**[Descargar los dos mapas en ZIP](https://github.com/miguelcoxcaballero/Inhouse-Game-Engine/raw/refs/heads/main/mapas-interactivos.zip)**

Descomprime el ZIP y abre uno de los HTML en Chrome, Edge o Firefox actualizado. Los mapas incluyen los datos y la biblioteca de visualización, por lo que funcionan sin conexión y no requieren instalación ni servidor.

| Archivo | Contenido |
| --- | --- |
| [valencia-interactivo.html](valencia-interactivo.html) | València con sus 87 barrios oficiales. |
| [atlas-valencia-chelva-cofrentes-albufera.html](atlas-valencia-chelva-cofrentes-albufera.html) | Atlas conjunto de València, Chelva, Cofrentes y l’Albufera, con sus alrededores. |
| [LEEME.txt](LEEME.txt) | Controles, cobertura y fuentes de datos. |
| [fuentes.json](fuentes.json) | Procedencia, fecha de los datos y áreas de cobertura. |

GitHub muestra los archivos HTML como código; para usar los mapas, descarga el ZIP o el archivo mediante **Download raw file** y ábrelo en el navegador.

## Explorar

- Desplazamiento y zoom, búsqueda de lugares y calles, e identificación mediante clic.
- Selector de zonas y controles para calles, límites, agua, zonas verdes y nombres.
- València dividida en 87 barrios oficiales; las otras zonas muestran límites municipales de OSM.
- Cofrentes se abre centrado en la central nuclear, con marcador destacado y un botón para ver los alrededores.
- Interfaz adaptable a escritorio y móvil.

![Vista general del atlas](previews/atlas-preview.png)

![Vista de Cofrentes centrada en la central](previews/cofrentes-preview.png)

## Datos y atribución

- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licencia ODbL. Extracto de [Geofabrik](https://download.geofabrik.de/europe/spain/valencia.html) del 25 de octubre de 2026.
- Barrios: [Ajuntament de València](https://opendata.vlci.valencia.es/dataset/barris-barrios), CC BY 4.0. Las 88 geometrías originales se agrupan en 87 códigos de barrio.
- Visualización: MapLibre GL JS 5.6.2, BSD-3-Clause.

Los recuadros indican las áreas de detalle descargadas, no límites administrativos. Entre zonas se conservan carreteras principales. Cartografía general para exploración; no incluye rutas, tráfico en directo ni un modelo 3D.

## Validación

Comprobados el cambio entre las cuatro zonas, la búsqueda, las capas, el enfoque de Cofrentes y la vista móvil. La prueba del navegador no registró errores ni solicitudes a servicios externos de mapas.
