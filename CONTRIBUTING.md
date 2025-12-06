# Guía de Contribución

¡Gracias por tu interés en contribuir a GeoWizard! 🎉

Este documento proporciona directrices para contribuir al proyecto. Al participar, te comprometes a mantener un ambiente respetuoso y colaborativo.

---

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
  - [Reportar Bugs](#reportar-bugs)
  - [Sugerir Mejoras](#sugerir-mejoras)
  - [Contribuir con Código](#contribuir-con-código)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)

---

## 📜 Código de Conducta

Este proyecto sigue un código de conducta para asegurar un ambiente acogedor. Al participar, se espera que:

- Uses lenguaje respetuoso e inclusivo
- Aceptes críticas constructivas con gracia
- Te enfoques en lo que es mejor para la comunidad
- Muestres empatía hacia otros miembros

---

## 🤝 ¿Cómo Puedo Contribuir?

### 🐛 Reportar Bugs

Si encuentras un bug, por favor:

1. **Verifica** que no haya sido reportado previamente en [Issues](https://github.com/tu-usuario/GeoWizard/issues)
2. **Crea un nuevo issue** con la etiqueta `bug`
3. **Incluye**:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs. actual
   - Sistema operativo y versión de Python
   - Capturas de pantalla si es relevante
   - Logs de error (si están disponibles)

**Plantilla de Bug Report:**

```markdown
**Descripción del Bug:**
[Descripción clara y concisa]

**Pasos para Reproducir:**
1. Ir a '...'
2. Hacer clic en '...'
3. Ingresar '...'
4. Ver error

**Comportamiento Esperado:**
[Lo que debería suceder]

**Comportamiento Actual:**
[Lo que realmente sucede]

**Entorno:**
- OS: [Windows 10, macOS 12, Ubuntu 20.04, etc.]
- Python: [3.8, 3.9, 3.10, etc.]
- GeoWizard: [versión]

**Logs/Capturas:**
[Adjuntar si es relevante]
```

---

### 💡 Sugerir Mejoras

Las sugerencias de nuevas características son bienvenidas:

1. **Verifica** que no haya una sugerencia similar en [Issues](https://github.com/tu-usuario/GeoWizard/issues)
2. **Crea un nuevo issue** con la etiqueta `enhancement`
3. **Describe**:
   - El problema que resuelve
   - La solución propuesta
   - Alternativas consideradas
   - Impacto en usuarios existentes

**Plantilla de Feature Request:**

```markdown
**Problema a Resolver:**
[¿Qué problema resuelve esta característica?]

**Solución Propuesta:**
[Describe tu solución ideal]

**Alternativas Consideradas:**
[¿Qué otras soluciones consideraste?]

**Contexto Adicional:**
[Capturas, mockups, ejemplos de uso]
```

---

### 💻 Contribuir con Código

#### Antes de Empezar

1. **Fork** el repositorio
2. **Clona** tu fork localmente
3. **Configura** el upstream:
   ```bash
   git remote add upstream https://github.com/tu-usuario/GeoWizard.git
   ```
4. **Crea una rama** para tu trabajo:
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

#### Durante el Desarrollo

1. **Escribe código limpio** siguiendo los [Estándares de Código](#estándares-de-código)
2. **Agrega tests** para nuevas características
3. **Actualiza documentación** si es necesario
4. **Commit con mensajes descriptivos**:
   ```bash
   git commit -m "feat: Agregar soporte para sistema de coordenadas XYZ"
   git commit -m "fix: Corregir cálculo de área en polígonos cóncavos"
   git commit -m "docs: Actualizar README con nueva funcionalidad"
   ```

#### Tipos de Commits (Conventional Commits)

- `feat:` Nueva característica
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato de código (no afecta funcionalidad)
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

---

## 📐 Estándares de Código

### Python (PEP 8)

Seguimos [PEP 8](https://pep8.org/) con algunas excepciones:

**Formato:**
- Indentación: 4 espacios (no tabs)
- Líneas: máximo 100 caracteres (120 para casos excepcionales)
- Encoding: UTF-8
- Docstrings: estilo Google en español

**Ejemplo de Código:**

```python
def calcular_area_utm(coords: List[Tuple[float, float]]) -> float:
    """
    Calcula el área de un polígono en coordenadas UTM.
    
    Args:
        coords: Lista de tuplas (x, y) en metros
        
    Returns:
        float: Área en metros cuadrados
        
    Raises:
        ValueError: Si hay menos de 3 coordenadas
    """
    if len(coords) < 3:
        raise ValueError("Se requieren al menos 3 coordenadas para un polígono")
    
    # Implementación usando la fórmula del área de Gauss
    area = 0.0
    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    
    return abs(area) / 2.0
```

**Nombres:**
- Clases: `PascalCase` (ej. `CoordinateManager`)
- Funciones/variables: `snake_case` (ej. `calculate_area`)
- Constantes: `UPPER_SNAKE_CASE` (ej. `MAX_ZOOM_LEVEL`)
- Privadas: prefijo `_` (ej. `_internal_method`)

**Imports:**
```python
# 1. Estándar library
import os
import sys
from pathlib import Path

# 2. Terceros
from PySide6.QtWidgets import QWidget
from pyproj import Transformer

# 3. Locales
from core.coordinate_manager import CoordinateManager
from utils.validators import validate_coordinate
```

---

### Linters y Herramientas

Recomendamos usar:

```bash
# Formatear código
black geowizard/

# Linting
flake8 geowizard/

# Type checking (opcional)
mypy geowizard/
```

---

## 🔄 Proceso de Pull Request

1. **Actualiza tu fork:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Asegúrate que todo funciona:**
   ```bash
   python test_measurements.py
   python test_coordinate_systems.py
   python test_closed_polygon.py
   ```

3. **Push a tu fork:**
   ```bash
   git push origin feature/nombre-descriptivo
   ```

4. **Abre un Pull Request:**
   - Título descriptivo
   - Descripción detallada de cambios
   - Referencias a issues relacionados (#123)
   - Capturas si hay cambios en UI

5. **Responde a reviews:**
   - Los mantenedores revisarán tu código
   - Responde a comentarios y haz ajustes si es necesario
   - Mantén la conversación profesional y constructiva

**Plantilla de Pull Request:**

```markdown
## Descripción
[Describe los cambios realizados]

## Tipo de Cambio
- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva característica (cambio que agrega funcionalidad)
- [ ] Breaking change (cambio que rompe compatibilidad)
- [ ] Documentación

## ¿Cómo Ha Sido Probado?
[Describe las pruebas realizadas]

## Checklist:
- [ ] Mi código sigue los estándares del proyecto
- [ ] He realizado auto-review de mi código
- [ ] He comentado código complejo
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan warnings
- [ ] He agregado tests que prueban mi corrección/funcionalidad
- [ ] Tests unitarios pasan localmente
- [ ] He actualizado CHANGELOG.md

## Issues Relacionados
Closes #(issue number)
```

---

## 🏗️ Estructura del Proyecto

```
GeoWizard/
├── core/                 # Lógica de negocio
│   ├── coordinate_manager.py  # Gestor de coordenadas
│   ├── geometry.py            # Construcción de geometrías
│   └── exceptions.py          # Excepciones personalizadas
│
├── ui/                   # Interfaz de usuario
│   ├── main_window.py         # Ventana principal
│   ├── coordinate_table.py    # Tabla de coordenadas
│   ├── editable_geometry.py   # Geometrías editables
│   └── validation_delegate.py # Validación en tabla
│
├── utils/                # Utilidades
│   ├── coordinate_systems.py  # Conversiones de coordenadas
│   ├── measurements.py        # Cálculos geométricos
│   ├── validators.py          # Validadores
│   ├── logger.py              # Sistema de logging
│   └── error_handler.py       # Manejo de errores
│
├── importers/            # Importadores
│   ├── csv_importer.py
│   ├── kml_importer.py
│   └── shapefile_importer.py
│
├── exporters/            # Exportadores
│   ├── kml_exporter.py
│   ├── kmz_exporter.py
│   └── shapefile_exporter.py
│
├── controllers/          # Controladores (MVC)
│   ├── coordinate_controller.py
│   └── file_controller.py
│
├── tests/                # Tests unitarios
│   └── test_importers.py
│
├── icons/                # Recursos SVG
├── leaflet/              # Librería Leaflet
└── main.py               # Punto de entrada
```

### Responsabilidades por Módulo

- **core/**: Lógica de negocio pura, sin dependencias de UI
- **ui/**: Componentes de interfaz, dependencias de PySide6
- **utils/**: Funciones auxiliares reutilizables
- **importers/exporters/**: Conversión de formatos
- **controllers/**: Intermediarios entre UI y lógica de negocio

---

## ⚙️ Configuración del Entorno de Desarrollo

### 1. Clonar y Configurar

```bash
git clone https://github.com/tu-usuario/GeoWizard.git
cd GeoWizard

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar herramientas de desarrollo (opcional)
pip install black flake8 mypy pytest
```

### 2. Configurar IDE

**VSCode:**
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.linting.flake8Args": [
    "--max-line-length=100"
  ]
}
```

**PyCharm:**
- File → Settings → Tools → Python Integrated Tools
- Docstring format: Google
- Code Style → Python → Tabs and Indents → 4 spaces

### 3. Ejecutar la Aplicación

```bash
python main.py
```

---

## 📞 Contacto

Si tienes preguntas:

- **Issues:** [GitHub Issues](https://github.com/tu-usuario/GeoWizard/issues)
- **Discusiones:** [GitHub Discussions](https://github.com/tu-usuario/GeoWizard/discussions)

---

## 🙏 Agradecimientos

¡Gracias por contribuir a GeoWizard! Tu ayuda hace que este proyecto sea mejor para todos. 🚀

---

**¡Happy Coding!** 💻✨
