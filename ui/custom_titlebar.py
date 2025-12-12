# ui/custom_titlebar.py
"""
Barra de título personalizada para ventanas de GeoWizard.
Soporta tema oscuro y claro, incluye logo de Tellus y botones minimalistas.
"""

from PySide6.QtCore import Qt, Signal, QPoint, QSize, QRect
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsColorizeEffect
from PySide6.QtGui import QPixmap, QIcon, QCursor, QColor, QPainter, QPainterPath, QRegion
import os
import sys


class CustomTitleBar(QWidget):
    """Barra de título personalizada con logo, título y botones de control."""
    
    closeClicked = Signal()
    minimizeClicked = Signal()
    maximizeClicked = Signal()
    
    def __init__(self, title="", parent=None, show_logo=True):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._dragging = False
        self._drag_position = QPoint()
        self._is_dark_mode = False
        self._show_logo = show_logo
        
        self._create_ui(title)
        self.set_dark_mode(False)  # Start with light mode
        # Aplicar máscara de esquinas redondeadas
        self._update_mask()
    
    def _create_ui(self, title):
        """Crea la interfaz de la barra de título."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(10)
        
        # Logo de Tellus (si se muestra)
        if self._show_logo:
            self.logo_label = QLabel()
            self.logo_label.setFixedSize(24, 24)
            self.logo_label.setScaledContents(False)
            self._load_logo()
            layout.addWidget(self.logo_label)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: normal; font-size: 12px;")  # Sin bold
        layout.addWidget(self.title_label, 1)
        
        # Botones de control
        button_size = 40  # Ligeramente más grande para iconos
        
        # Botón minimizar
        self.btn_minimize = QPushButton()
        self.btn_minimize.setFixedSize(button_size, button_size)
        self.btn_minimize.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_minimize.clicked.connect(self.minimizeClicked)
        self.btn_minimize.setToolTip("Minimizar")
        self._set_button_icon(self.btn_minimize, "minimize.svg")
        layout.addWidget(self.btn_minimize)
        
        # Botón maximizar/restaurar
        self.btn_maximize = QPushButton()
        self.btn_maximize.setFixedSize(button_size, button_size)
        self.btn_maximize.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_maximize.clicked.connect(self.maximizeClicked)
        self.btn_maximize.setToolTip("Maximizar")
        self._set_button_icon(self.btn_maximize, "maximize.svg")
        layout.addWidget(self.btn_maximize)
        
        # Botón cerrar
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(button_size, button_size)
        self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close.clicked.connect(self.closeClicked)
        self.btn_close.setToolTip("Cerrar")
        self._set_button_icon(self.btn_close, "Close.svg")
        layout.addWidget(self.btn_close)
    
    def _set_button_icon(self, button, icon_name):
        """Establece el icono SVG para un botón."""
        try:
            # Usar la misma lógica para encontrar los iconos
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                current_file = os.path.abspath(__file__)
                ui_dir = os.path.dirname(current_file)
                base_path = os.path.dirname(ui_dir)
            
            icon_path = os.path.join(base_path, "icons", "titlebar", icon_name)
            
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                button.setIcon(icon)
                button.setIconSize(QSize(16, 16))  # Tamaño del icono
            else:
                print(f"Icon not found: {icon_path}")
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_logo(self):
        """Carga el logo de Tellus Consultoría."""
        try:
            # Usar la misma lógica que MainWindow para encontrar el logo
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                # Ir dos niveles arriba desde ui/ para llegar a la raíz del proyecto
                current_file = os.path.abspath(__file__)
                ui_dir = os.path.dirname(current_file)
                base_path = os.path.dirname(ui_dir)
            
            logo_path = os.path.join(base_path, "icons", "tellus_logo.png")
            
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                else:
                    print(f"Logo pixmap is null: {logo_path}")
            else:
                print(f"Logo not found at: {logo_path}")
                # Intentar ruta alternativa
                alt_path = os.path.join(os.path.dirname(base_path), "icons", "tellus_logo.png")
                if os.path.exists(alt_path):
                    pixmap = QPixmap(alt_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.logo_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error loading logo for title bar: {e}")
            import traceback
            traceback.print_exc()
    
    def set_dark_mode(self, dark):
        """Aplica el tema oscuro o claro a la barra de título."""
        self._is_dark_mode = dark
        
        if dark:
            # Tema oscuro
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            button_hover = "#3d3d3d"
            button_pressed = "#505050"
            close_hover = "#c42b1c"
            close_pressed = "#a52313"
        else:
            # Tema claro
            bg_color = "#f0f0f0"
            text_color = "#000000"
            button_hover = "#e0e0e0"
            button_pressed = "#d0d0d0"
            close_hover = "#e81123"
            close_pressed = "#c42b1c"
        
        # Estilo general de la barra con esquinas redondeadas
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {bg_color};
                border-bottom: 1px solid {"#3d3d3d" if dark else "#d0d0d0"};
            }}
        """)
        
        # Estilo del título
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-weight: normal;
                font-size: 12px;
            }}
        """)
        
        # Aplicar filtros de color a los iconos según el tema
        self._apply_icon_filters(dark)
        
        # Estilos de botones minimizar y maximizar
        button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
        """
        
        self.btn_minimize.setStyleSheet(button_style)
        self.btn_maximize.setStyleSheet(button_style)
        
        # Estilo especial para botón cerrar (rojo al hacer hover)
        close_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {close_hover};
            }}
            QPushButton:pressed {{
                background-color: {close_pressed};
            }}
        """
        
        self.btn_close.setStyleSheet(close_style)
    
    def _apply_icon_filters(self, dark):
        """Aplica filtros de color a los iconos según el tema."""
        if dark:
            # En modo oscuro, colorizar los iconos a blanco/gris claro
            for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor(220, 220, 220))  # Gris claro
                effect.setStrength(1.0)  # Colorización completa
                btn.setGraphicsEffect(effect)
        else:
            # En modo claro, quitar filtros (usar colores originales)
            for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
                btn.setGraphicsEffect(None)
    
    def set_title(self, title):
        """Cambia el título de la ventana."""
        self.title_label.setText(title)
    
    def update_maximize_button(self, is_maximized):
        """Actualiza el icono del botón maximizar/restaurar."""
        # Mantener el mismo icono (maximize.svg funciona para ambos estados)
        # Si el usuario proporciona un icono "restore.svg", podemos usarlo aquí
        if is_maximized:
            self.btn_maximize.setToolTip("Restaurar")
        else:
            self.btn_maximize.setToolTip("Maximizar")
    
    def mousePressEvent(self, event):
        """Maneja el inicio del arrastre de la ventana."""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Arrastra la ventana."""
        if self._dragging and event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Finaliza el arrastre."""
        self._dragging = False
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Doble clic para maximizar/restaurar."""
        if event.button() == Qt.LeftButton:
            self.maximizeClicked.emit()
            event.accept()
    
    def resizeEvent(self, event):
        """Actualiza la máscara cuando cambia el tamaño."""
        super().resizeEvent(event)
        self._update_mask()
    
    def _update_mask(self):
        """Aplica una máscara para recortar las esquinas superiores."""
        # Crear path con esquinas redondeadas
        path = QPainterPath()
        rect = QRect(0, 0, self.width(), self.height())
        radius = 8
        
        # Añadir rectángulo con esquinas superiores redondeadas
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + radius)
        path.arcTo(rect.left(), rect.top(), radius * 2, radius * 2, 180, -90)
        path.lineTo(rect.right() - radius, rect.top())
        path.arcTo(rect.right() - radius * 2, rect.top(), radius * 2, radius * 2, 90, -90)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        
        # Convertir path a región y aplicar como máscara
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
