# Referencia visual: State of Leonida

Consulta y descarga local:2026-10-26. Sitio identificado: [map.stateofleonida.net/en/](https://map.stateofleonida.net/en/).

Se descargaron para inspección el HTML público y los recursos CSS/JavaScript propios referenciados por esa página. También se abrió la página en Chromium y se inspeccionó su apariencia y sus controles. La copia de referencia permanece fuera del repositorio; no se redistribuyen el código propio, imágenes de Rockstar, logos, fondos ni teselas de ese proyecto.

No se encontró una licencia de reutilización íntegra del código propio en la página, los archivos inspeccionados o la búsqueda de su repositorio. Por ello **la UI de Isla Levante es una implementación propia**, no el mismo código solicitado. Se informó de esta limitación durante el trabajo. Una licencia o permiso del titular permitiría reconsiderar ese requisito.

Se tomaron como referencia funcional: mapa dominante a pantalla completa, herramientas flotantes, paneles plegables, búsqueda, filtros, agrupación de marcadores, ajustes de apariencia, medición y dibujo. Se implementaron con MapLibre y código local, conservando la atribución y licencia de la biblioteca.

Para el detalle cartográfico se añadieron huellas de edificios enteras, cobertura forestal de diseño, textura del relieve, curvas de nivel, referencias cotidianas OSM, nombres de calles al acercar, corredores completos de autovía, nuevo cauce, taludes y cruces. **No se declara alcanzada una equivalencia de detalle ni realismo con el proyecto comunitario**: falta una revisión visual sistemática a varias escalas y un diseño fino de costa, barrios y conexiones. El resultado es una nueva versión revisable, no un nivel de juego terminado.

## Nuevo cauce del Turia

Hecho documentado: la CHJ identifica la masa «Río Turia: nuevo cauce–mar» desde el azud de reparto hasta el Mediterráneo, separada del antiguo cauce urbano. Fuente: [Plan Hidrológico2022–2027, anejo de masas modificadas](https://www.chj.es/es-es/medioambiente/planificacionhidrologica/Documents/Plan-Hidrologico-cuenca-2021-2027/PHC/Version%20Final/PHJ2227_Anejo01_MAMM_ARTIF_2023_01_24.pdf), documento2023, consultado2026-10-26.

La documentación histórica del [Plan Sur alojada en UPV](https://victoryepes.blogs.upv.es/files/2024/11/IMPULSO-A-VALENCIA_ACTUALIZACION-DEL-PLAN-SUR-DE-VALENCIA.pdf) describe la evolución de los viales marginales a la V-30. El [BOE de24-06-2026](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-21517) publica la aprobación de un proyecto de conexión V-30/A-3 mediante puente; eso no demuestra que el proyecto esté construido.

Propuesta de diseño: corredor sur compacto con lecho, taludes, hilo de agua conceptual, V-30 en las márgenes y cruces seleccionados. La geometría procede de la secuencia de un corredor vial OSM adaptado; no es el contorno hidráulico real. No se representan caudales, avenidas, riesgo de inundación ni capacidad de desagüe.
