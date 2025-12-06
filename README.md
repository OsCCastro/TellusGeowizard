# 🗺️ GeoWizard

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)

**Una aplicación de escritorio profesional para la gestión y visualización de coordenadas geográficas**

</div>

---

## 📋 Descripción

GeoWizard es una herramienta de escritorio desarrollada en Python que permite a profesionales y entusiastas de la geomática gestionar coordenadas geográficas de manera eficiente. La aplicación ofrece una interfaz intuitiva para ingresar, visualizar, editar y exportar datos geoespaciales en múltiples sistemas de coordenadas.

### ✨ Características Principales

#### ✅ **Sistemas de Coordenadas Múltiples**
- 🌐 UTM (Universal Transverse Mercator)
- 🌍 Geográficas (Grados Decimales)
- 🧭 Geográficas (Grados, Minutos, Segundos - DMS)
- 🗺️ Web Mercator

#### ✅ **Gestión de Geometrías**
- 📍 Puntos
- 📏 Polilíneas
- ⬟ Polígonos
- ✏️ Edición interactiva en mapa
- 🎯 Validación en tiempo real

#### ✅ **Visualización Avanzada**
- 🗺️ Mapa base OpenStreetMap integrado
- 🎨 Lienzo de dibujo vectorial
- 🔍 Zoom y navegación interactiva
- 🌓 Modo claro/oscuro
- 📐 Cálculo de mediciones (área, perímetro, distancia)

#### ✅ **Importación/Exportación**
- 📥 **Importar desde:**
  - CSV
  - KML (Keyhole Markup Language)
  - Shapefile (ESRI)
  
- 📤 **Exportar a:**
  - KML
  - KMZ (KML comprimido)
  - Shapefile
  - CSV
  - HTML (resumen con mediciones)

#### ✅ **Funcionalidades Adicionales**
- 🔄 Transformación automática entre sistemas de coordenadas
- 📊 Tabla editable de coordenadas
- ↩️ Deshacer/Rehacer
- 📸 Captura de pantalla del mapa
- ⚙️ Configuraciones personalizables

---

## 🖼️ Capturas de Pantalla

*[Puedes agregar capturas de pantalla de tu aplicación aquí]*

---

## 💻 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo:** Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python:** 3.7 o superior
- **RAM:** 2 GB (4 GB recomendado)
- **Espacio en disco:** 200 MB

### Dependencias
- PySide6 6.0+ (Framework Qt)
- pyproj 3.0+ (Transformaciones de coordenadas)
- fiona 1.8+ (I/O de formatos geoespaciales)
- pyshp 2.1+ (Shapefiles)
- lxml 4.6+ (Parsing XML/KML)

---

## 🚀 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/GeoWizard.git
cd GeoWizard
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\\Scripts\\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la Aplicación
```bash
python main.py
```

---

## 📖 Uso

### Inicio Rápido

1. **Seleccionar Sistema de Coordenadas:**
   - Elige el sistema de coordenadas deseado en el desplegable
   - Para UTM, selecciona hemisferio y zona

2. **Ingresar Coordenadas:**
   - Escribe las coordenadas directamente en la tabla
   - O pega datos desde el portapapeles
   - La validación en tiempo real muestra errores en rojo

3. **Seleccionar Geometría:**
   - Marca el tipo: Punto, Polilínea o Polígono
   - La visualización se actualiza automáticamente

4. **Visualizar:**
   - Activa el **mapa base OSM** para ver en contexto geográfico
   - O usa el **lienzo vectorial** para dibujo técnico
   - Alterna con el botón en la barra de herramientas

5. **Editar Geometrías:**
   - Activa el **modo de edición** en la barra de herramientas
   - Arrastra puntos en el mapa para ajustar posiciones
   - Los cambios se sincronizan con la tabla

6. **Exportar:**
   - Ingresa nombre del proyecto
   - Selecciona formato (.kml, .kmz, .shp)
   - Elige carpeta de destino
   - ¡Listo!

### Importar Datos Existentes

```
Archivo → Importar → Seleccionar archivo (CSV/KML/SHP)
```

La aplicación detectará automáticamente:
- Sistema de coordenadas (si está definido)
- Tipo de geometría
- Atributos asociados

---

## 🛠️ Tecnologías Utilizadas

| Tecnología | Propósito |
|------------|-----------|
| **Python 3.7+** | Lenguaje de programación principal |
| **PySide6 (Qt)** | Framework de interfaz gráfica |
| **pyproj** | Transformaciones geodésicas y cartográficas |
| **fiona** | Lectura/escritura de formatos geoespaciales |
| **pyshp** | Manejo de shapefiles ESRI |
| **lxml** | Parsing y generación de KML/XML |
| **Leaflet.js** | Visualización de mapas interactivos |
| **OpenStreetMap** | Tiles de mapa base |

---

## 📁 Estructura del Proyecto

```
GeoWizard/
├── core/                 # Lógica de negocio principal
│   ├── coordinate_manager.py
│   ├── geometry.py
│   └── exceptions.py
├── ui/                   # Componentes de interfaz
│   ├── main_window.py
│   ├── coordinate_table.py
│   ├── editable_geometry.py
│   └── validation_delegate.py
├── utils/                # Utilidades
│   ├── coordinate_systems.py
│   ├── measurements.py
│   ├── validators.py
│   └── logger.py
├── importers/            # Módulos de importación
│   ├── csv_importer.py
│   ├── kml_importer.py
│   └── shapefile_importer.py
├── exporters/            # Módulos de exportación
│   ├── kml_exporter.py
│   ├── kmz_exporter.py
│   └── shapefile_exporter.py
├── controllers/          # Controladores
├── icons/                # Iconos SVG
├── leaflet/              # Librería Leaflet
├── tests/                # Tests unitarios
├── main.py               # Punto de entrada
├── gui.py                # GUI principal (legacy)
├── requirements.txt      # Dependencias
├── LICENSE               # Licencia MIT
└── README.md             # Este archivo
```

---

## 🧪 Testing

Ejecutar tests unitarios:

```bash
# Test de mediciones
python test_measurements.py

# Test de sistemas de coordenadas
python test_coordinate_systems.py

# Test de polígonos cerrados
python test_closed_polygon.py

# Verificación de correcciones
python verify_fix.py
```

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor, consulta [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles sobre:

- Cómo reportar bugs
- Cómo proponer nuevas características
- Estándares de código
- Proceso de Pull Requests

### Guía Rápida para Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2025 GeoWizard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contacto y Soporte

- **Issues:** [GitHub Issues](https://github.com/tu-usuario/GeoWizard/issues)
- **Discusiones:** [GitHub Discussions](https://github.com/tu-usuario/GeoWizard/discussions)

---

## 🗺️ Roadmap

### Versión 1.1 (Planificada)
- [ ] Soporte para más sistemas de coordenadas (State Plane, etc.)
- [ ] Importación de GeoJSON
- [ ] Exportación a DXF (AutoCAD)
- [ ] Calculadora de áreas compuestas
- [ ] Herramientas de análisis espacial básicas

### Versión 2.0 (Futura)
- [ ] Base de datos interna para proyectos
- [ ] Análisis de rede vial
- [ ] Integración con servicios WMS/WFS
- [ ] Editor de estilos avanzado
- [ ] API para plugins

---

## 🙏 Agradecimientos

- **OpenStreetMap** - Por los tiles de mapa base
- **Leaflet.js** - Por la librería de mapas interactivos
- **Qt Project** - Por el framework Qt/PySide6
- **PROJ** - Por las transformaciones geodésicas

---

<div align="center">

**Desarrollado con ❤️ para la comunidad geoespacial**

⭐ Si te gusta este proyecto, ¡dale una estrella en GitHub! ⭐

</div>