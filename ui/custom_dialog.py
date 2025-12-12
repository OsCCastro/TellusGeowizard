# ui/custom_dialog.py
"""
Clase base para diálogos con barra de título personalizada.
Proporciona funcionalidad consistente para todas las ventanas de GeoWizard.
"""

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from ui.custom_titlebar import CustomTitleBar


class CustomDialog(QDialog):
    """Diálogo base con barra de título personalizada y soporte de temas."""
    
    def __init__(self, title="", parent=None, show_logo=True):
        super().__init__(parent)
        
        # Configurar ventana sin marco
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        # NO usar TranslucentBackground para evitar bordes blancos
        # self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._is_dark_mode = False
        self._is_maximized = False
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Sin márgenes externos
        main_layout.setSpacing(0)
        
        # Container con bordes redondeados
        self.container = QWidget()
        self.container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Barra de título
        self.title_bar = CustomTitleBar(title, self, show_logo=show_logo)
        self.title_bar.closeClicked.connect(self.close)
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.maximizeClicked.connect(self._toggle_maximize)
        container_layout.addWidget(self.title_bar)
        
        # Área de contenido
        self.content_widget = QWidget()
        self.content_widget.setObjectName("dialogContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)  # Reducido de 15 a 12
        container_layout.addWidget(self.content_widget)
        
        main_layout.addWidget(self.container)
        
        # Aplicar sombra
        self._apply_shadow()
        
        # Aplicar estilos iniciales
        self.set_dark_mode(False)
    
    def _apply_shadow(self):
        """Aplica sombra al diálogo para efecto flotante."""
        # No aplicar sombra cuando no hay fondo translucent, causa bordes blancos
        # shadow = QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(15)
        # shadow.setXOffset(0)
        # shadow.setYOffset(2)
        # shadow.setColor(QColor(0, 0, 0, 60))
        # self.container.setGraphicsEffect(shadow)
        pass  # Deshabilitado para evitar bordes blancos
    
    def _toggle_maximize(self):
        """Alterna entre maximizado y normal."""
        if self.isMaximized():
            self.showNormal()
            self._is_maximized = False
        else:
            self.showMaximized()
            self._is_maximized = True
        
        self.title_bar.update_maximize_button(self._is_maximized)
    
    def set_dark_mode(self, dark):
        """Aplica el tema oscuro o claro al diálogo completo."""
        self._is_dark_mode = dark
        
        # Actualizar barra de título
        self.title_bar.set_dark_mode(dark)
        
        # Colores según tema
        if dark:
            bg_color = "#2b2b2b"  # Mismo color que la barra de título
            content_bg = "#1e1e1e"  # Ligeramente más oscuro
            text_color = "#ffffff"
            border_color = "#3d3d3d"
        else:
            bg_color = "#f0f0f0"  # Mismo color que la barra de título
            content_bg = "#ffffff"  # Blanco puro
            text_color = "#000000"
            border_color = "#d0d0d0"
        
        # Aplicar color de fondo al diálogo principal para eliminar bordes blancos
        self.setStyleSheet(f"""
            CustomDialog {{
                background-color: {bg_color};
            }}
        """)
        # Aplicar estilos al container (sin border para evitar píxeles blancos)
        self.container.setStyleSheet(f"""
            QWidget#dialogContainer {{
                background-color: {bg_color};
                border: none;
                border-radius: 8px;
            }}
            QWidget#dialogContent {{
                background-color: {content_bg};
                color: {text_color};
            }}
        """)
    
    def set_title(self, title):
        """Cambia el título de la ventana."""
        self.title_bar.set_title(title)
    
    def changeEvent(self, event):
        """Maneja cambios de estado de la ventana."""
        if event.type() == QEvent.WindowStateChange:
            self.title_bar.update_maximize_button(self.isMaximized())
        super().changeEvent(event)
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento para ajustar sombra."""
        super().resizeEvent(event)
        # Actualizar sombra cuando cambia el tamaño
        if self.isMaximized():
            # Sin sombra cuando está maximizado
            self.container.setGraphicsEffect(None)
        else:
            # Restaurar sombra cuando está en modo normal
            if not self.container.graphicsEffect():
                self._apply_shadow()
