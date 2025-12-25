# core/geometry.py
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF

class GeometryBuilder:
    """
    Construye objetos de dibujo (QPainterPath) a partir
    de la lista de features que devuelve CoordinateManager.
    """

    @staticmethod
    def paths_from_features(features: list[dict]):
        """
        Devuelve lista de tuplas (path: QPainterPath, pen: QPen)
        para cada feature.
        """
        result = []
        from PySide6.QtGui import QPen
        from PySide6.QtCore import Qt

        for feat in features:
            pts = feat["coords"]
            typ = feat["type"]

            # cerrar anillo solo en Polígono
            if typ == "Polígono":
                pts = pts + [pts[0]]
            path = QPainterPath(QPointF(*pts[0]))
            for x,y in pts[1:]:
                path.lineTo(x,y)

            # definir estilo
            if typ == "Punto":
                # en GUI dibujaremos un pequeño círculo, no via path
                continue
            elif typ == "Polilínea":
                pen = QPen(Qt.blue, 2)
            else:  # Polígono
                pen = QPen(Qt.green, 1)
                pen.setStyle(Qt.SolidLine)

            result.append((path, pen))
        return result
