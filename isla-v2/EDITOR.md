# Editor de sugerencias de Levante

Abre **isla-levante-editor.html** en Chrome, Edge o Firefox actualizado. Es un único archivo: incluye el mapa, los datos y las herramientas, y funciona sin conexión. Utiliza la misma instantánea de mapa publicada en `8b3b342`; las pruebas de densificación posteriores no sustituyen esta base de revisión.

## Edificios

- En **Edificios**, pulsa una huella y arrástrala.
- **Mayús + clic** añade o quita edificios de la selección. También puedes activar **Acumular selección**.
- En **Recuadro**, arrastra un rectángulo para seleccionar varias huellas. Vuelve a **Edificios** y arrastra cualquiera de las seleccionadas para mover todo el grupo.
- **Seleccionar conjunto** añade las piezas del mismo conjunto del mapa; comprueba la selección resaltada antes de arrastrar.
- Las flechas del teclado mueven una selección 1 m; Mayús + flecha, 10 m. Se conserva la forma y el tamaño de todas las huellas. El movimiento de un grupo conserva sus distancias internas.
- Los contornos discontinuos señalan las posiciones originales; los edificios modificados aparecen en turquesa y los seleccionados en rosa.
- **Restaurar posiciones seleccionadas** devuelve solo esos edificios a su ubicación de partida. Deshacer y rehacer funcionan con movimientos, calles e importaciones. Las notas generales se conservan al deshacer geometría.

## Calles

**Calle por puntos** permite dibujar un recorrido con clics. Añade puntos para indicar curvas y termina con **Terminar calle** o Enter. **Trazo libre** permite dibujar manteniendo pulsado; el recorrido se guarda al soltar.

Cada propuesta admite nombre, tipo de vía, ancho en metros y una explicación. Para modificar sus detalles, selecciónala en la lista y pulsa **Guardar detalles**. Puedes eliminar propuestas y deshacer la eliminación. Los trazos son sugerencias: todavía no sustituyen calles existentes ni verifican cruces o colisiones.

## Pasar las indicaciones al chat

Pulsa **Exportar ficha JSON** y adjunta el archivo descargado en el chat. Incluye:

- El identificador de la versión de mapa utilizada.
- Los edificios movidos, sus identificadores OSM cuando existen, geometrías originales y propuestas y desplazamientos en metros.
- Las calles dibujadas con sus puntos, anchos y notas.
- Tus indicaciones generales.

El editor guarda los cambios localmente cuando el navegador lo permite. Exportar la ficha crea una copia transportable: **Importar ficha** permite continuar en otro navegador o recuperar esa copia. La importación rechaza fichas de otra versión del mapa para evitar mover edificios equivocados. Importar sustituye la propuesta abierta y se puede deshacer.

**Espacio + arrastrar** mueve el mapa sin abandonar la herramienta. **Esc** cancela el trazo pendiente o deselecciona. El botón **Panel** oculta los controles para dejar más espacio, especialmente en móvil.

## Contrato de datos

Formato `levante-feedback`, versión de esquema `1`. `base_map.payload_sha256` identifica exactamente el contenido de mapa del HTML; `base_feature_index` y `edit_id` identifican cada instancia, incluso si varias comparten un ID OSM. `building_moves` contiene traslaciones respecto a la base, no desplazamientos acumulativos que deban repetirse. `street_suggestions` es una colección de entidades en **metros locales de la isla ficticia**, no coordenadas geográficas. `editor_state` permite recuperar la propuesta en este editor.

Se debe aplicar `translation_m` a la geometría métrica original de la versión correspondiente. Las geometrías de la ficha sirven también para inspección y comparación. Las propuestas no modifican los datos originales del repositorio ni OpenStreetMap.

## Reproducción y comprobaciones

`python source/build_editor.py` crea el editor a partir del HTML estable existente, sin reconstruir la geografía en desarrollo. `source/qa_editor.cjs` comprueba con un navegador real: selección múltiple y por recuadro, arrastre de grupos, conservación de huellas, deshacer/rehacer, ambos modos de dibujo, descarga de ficha, importación, rechazo de versiones incompatibles, texto literal, persistencia y diseño móvil. El resultado está en `data/editor-browser-qa.json`.
