# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2025-12-05

### 🎉 Lanzamiento Inicial

Primera versión estable de GeoWizard con funcionalidad completa para gestión de coordenadas geográficas.

### ✨ Añadido

#### Sistemas de Coordenadas
- Soporte para UTM (Universal Transverse Mercator)
- Soporte para coordenadas geográficas en grados decimales
- Soporte para coordenadas geográficas en DMS (Grados, Minutos, Segundos)
- Soporte para Web Mercator
- Conversión automática entre todos los sistemas soportados
- Selección de zona UTM (1-60) y hemisferio (Norte/Sur)

#### Gestión de Geometrías
- Creación de puntos individuales
- Creación de polilíneas
- Creación de polígonos
- Modo de edición interactiva con arrastre de vértices
- Sincronización automática tabla-mapa
- Validación en tiempo real de coordenadas

#### Visualización
- Mapa base interactivo con OpenStreetMap
- Lienzo de dibujo vectorial para representación técnica
- Zoom y navegación con mouse
- Modo claro/oscuro
- Visualización de geometrías con estilos diferenciados

#### Mediciones
- Cálculo de áreas (m², ha, km², acres, sq ft)
- Cálculo de perímetros
- Cálculo de distancias
- Soporte para unidades métricas e imperiales
- Precisión según sistema de coordenadas:
  - Planar (UTM): cálculos precisos en metros
  - Geodésico (Geográficas): cálculos en elipsoide WGS84

#### Importación
- Importación desde archivos CSV
- Importación desde archivos KML
- Importación desde Shapefiles (.shp)
- Detección automática de sistema de coordenadas
- Conversión automática a sistema de trabajo actual

#### Exportación
- Exportación a KML (Google Earth)
- Exportación a KMZ (KML comprimido)
- Exportación a Shapefile (ESRI)
- Exportación a CSV
- Generación de resumen HTML con mediciones

#### Interfaz de Usuario
- Tabla editable de coordenadas con validación en línea
- Toolbars con iconos SVG adaptativos
- Validación visual de campos inválidos (bordes rojos)
- Tooltips informativos para campos incorrectos
- Menú contextual para operaciones en tabla
- Soporte para copiar/pegar desde Excel y otras fuentes

#### Arquitectura y Calidad de Código
- Arquitectura modular (core, ui, utils, importers, exporters)
- Manejo centralizado de excepciones personalizadas
- Sistema de logging configurable
- Validadores reutilizables
- Decoradores para manejo de errores
- Separación de responsabilidades (MVC-like)

### 🔧 Configuración
- Diálogo de configuraciones para personalización
- Configuración de escala de dibujo
- Configuración de tamaño de puntos
- Configuración de tamaño de fuente

### 📚 Documentación
- README.md completo con guías de instalación y uso
- CONTRIBUTING.md para guía de contribuidores
- Docstrings en español en todos los módulos
- Comentarios explicativos en código complejo
- Tests unitarios para mediciones y validaciones

### 🧪 Testing
- Tests para cálculos de mediciones
- Tests para conversión de sistemas de coordenadas
- Tests para polígonos cerrados
- Scripts de verificación de correcciones

---

## [Unreleased]

### 🚧 En Desarrollo
- Soporte para más sistemas de coordenadas (State Plane)
- Importación/exportación de GeoJSON
- Exportación a DXF (AutoCAD)
- Herramientas de análisis espacial

---

## Leyenda de Tipos de Cambios

- `✨ Añadido` para nuevas características
- `🔧 Cambiado` para cambios en funcionalidad existente
- `🐛 Corregido` para corrección de bugs
- `🗑️ Eliminado` para características eliminadas
- `🔒 Seguridad` para correcciones de seguridad
- `⚡ Rendimiento` para mejoras de rendimiento
- `📚 Documentación` para cambios en documentación

---

## Versionado

Este proyecto sigue [Semantic Versioning](https://semver.org/):

- **MAJOR** versión cuando hay cambios incompatibles en la API
- **MINOR** versión cuando se añade funcionalidad de manera compatible
- **PATCH** versión cuando se corrigen bugs de manera compatible

Formato: `MAJOR.MINOR.PATCH`

---

[1.0.0]: https://github.com/tu-usuario/GeoWizard/releases/tag/v1.0.0
[Unreleased]: https://github.com/tu-usuario/GeoWizard/compare/v1.0.0...HEAD
