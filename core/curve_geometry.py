"""
Módulo para representar y procesar segmentos curvos en geometrías topográficas.
"""
import math
import re
from typing import Tuple, List, Optional


class CurveSegment:
    """
    Representa un segmento curvo definido por parámetros topográficos.
    
    Los parámetros principales son:
    - Punto inicial y final
    - Centro del arco circular
    - Delta (ángulo de deflexión)
    - Radio del arco
    - Dirección (horario/antihorario)
    """
    
    def __init__(
        self,
        start_point: Tuple[float, float],
        end_point: Optional[Tuple[float, float]] = None,
        center: Tuple[float, float] = None,
        delta: str = None,
        radius: float = None,
        clockwise: bool = True
    ):
        """
        Inicializa un segmento curvo.
        
        Args:
            start_point: (x, y) punto inicial del arco
            end_point: (x, y) punto final del arco (opcional si se calcula)
            center: (x, y) centro del círculo
            delta: Ángulo de deflexión (formato DMS "05°5'5.56\"" o decimal "5.085")
            radius: Radio del arco en metros
            clockwise: True = curva a la derecha (horario), False = curva a la izquierda (antihorario)
        """
        self.start_point = start_point
        self.end_point = end_point
        self.center = center
        self._delta_str = delta
        self.delta_degrees = self._parse_delta(delta) if delta else None
        self.radius = radius
        self.clockwise = clockwise
    
    @staticmethod
    def _parse_delta(delta_str: str) -> float:
        """
        Parsea el ángulo delta desde formato DMS o decimal.
        
        Soporta formatos:
        - DMS: "05°5'5.56\"" o "05d05m05.56s"
        - Decimal: "5.085" o "5.085°"
        
        Returns:
            Ángulo en grados decimales
        """
        delta_str = delta_str.strip()
        
        # Intenta formato decimal primero
        decimal_match = re.match(r'^([\d.]+)°?$', delta_str)
        if decimal_match:
            return float(decimal_match.group(1))
        
        # Formato DMS con símbolos °'"
        dms_match = re.match(
            r"(\d+)°\s*(\d+)'\s*([\d.]+)\"",
            delta_str
        )
        if dms_match:
            degrees = int(dms_match.group(1))
            minutes = int(dms_match.group(2))
            seconds = float(dms_match.group(3))
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # Formato DMS alternativo (d m s)
        dms_alt_match = re.match(
            r"(\d+)d\s*(\d+)m\s*([\d.]+)s",
            delta_str,
            re.IGNORECASE
        )
        if dms_alt_match:
            degrees = int(dms_alt_match.group(1))
            minutes = int(dms_alt_match.group(2))
            seconds = float(dms_alt_match.group(3))
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        raise ValueError(f"Formato de delta no reconocido: {delta_str}")
    
    def calculate_arc_length(self) -> float:
        """
        Calcula la longitud del arco.
        
        Returns:
            Longitud del arco en metros
        """
        if not self.radius or not self.delta_degrees:
            raise ValueError("Radio y delta son requeridos para calcular longitud")
        
        # L = r * θ (θ en radianes)
        theta_rad = math.radians(self.delta_degrees)
        return self.radius * theta_rad
    
    def calculate_subtangent(self) -> float:
        """
        Calcula la subtangente (ST) de la curva.
        
        ST = R * tan(Δ/2)
        
        Returns:
            Subtangente en metros
        """
        if not self.radius or not self.delta_degrees:
            raise ValueError("Radio y delta son requeridos para calcular subtangente")
        
        half_delta_rad = math.radians(self.delta_degrees / 2)
        return self.radius * math.tan(half_delta_rad)
    
    def calculate_tangent_external(self) -> float:
        """
        Calcula la tangente externa (E) de la curva.
        
        E = R * (1/cos(Δ/2) - 1) = R * (sec(Δ/2) - 1)
        
        Returns:
            Tangente externa en metros
        """
        if not self.radius or not self.delta_degrees:
            raise ValueError("Radio y delta son requeridos para calcular tangente externa")
        
        half_delta_rad = math.radians(self.delta_degrees / 2)
        return self.radius * (1 / math.cos(half_delta_rad) - 1)
    
    def calculate_chord_length(self) -> float:
        """
        Calcula la cuerda larga (C) de la curva.
        
        C = 2 * R * sin(Δ/2)
        
        Returns:
            Longitud de la cuerda en metros
        """
        if not self.radius or not self.delta_degrees:
            raise ValueError("Radio y delta son requeridos para calcular cuerda")
        
        half_delta_rad = math.radians(self.delta_degrees / 2)
        return 2 * self.radius * math.sin(half_delta_rad)
    
    def calculate_middle_ordinate(self) -> float:
        """
        Calcula la ordenada media (M) de la curva.
        
        M = R * (1 - cos(Δ/2))
        
        Returns:
            Ordenada media en metros
        """
        if not self.radius or not self.delta_degrees:
            raise ValueError("Radio y delta son requeridos para calcular ordenada media")
        
        half_delta_rad = math.radians(self.delta_degrees / 2)
        return self.radius * (1 - math.cos(half_delta_rad))
    
    def densify(self, num_points: int = 15) -> List[Tuple[float, float]]:
        """
        Genera puntos intermedios a lo largo del arco.
        
        Args:
            num_points: Número de puntos intermedios a generar (default: 15)
        
        Returns:
            Lista de (x, y) puntos a lo largo del arco
        """
        if not all([self.start_point, self.center, self.radius, self.delta_degrees]):
            raise ValueError("Parámetros incompletos para densificar curva")
        
        cx, cy = self.center
        sx, sy = self.start_point
        
        # Calcular ángulo inicial desde el centro hacia el punto de inicio
        start_angle = math.atan2(sy - cy, sx - cx)
        
        # Convertir delta a radianes
        delta_rad = math.radians(self.delta_degrees)
        
        # Determinar dirección basada en la posición relativa
        # En topografía, las curvas generalmente siguen la dirección de la poligonal
        # Usamos sentido horario (-1) como predeterminado para curvas a la derecha
        direction = getattr(self, 'clockwise', True)
        dir_mult = -1 if direction else 1  # -1 = horario, 1 = antihorario
        
        # Si hay punto final definido, determinar dirección automáticamente
        if self.end_point:
            ex, ey = self.end_point
            end_angle = math.atan2(ey - cy, ex - cx)
            
            # Calcular diferencia angular
            angle_diff_cw = (start_angle - end_angle) % (2 * math.pi)
            angle_diff_ccw = (end_angle - start_angle) % (2 * math.pi)
            
            # Elegir la dirección que coincida mejor con delta
            if abs(angle_diff_cw - delta_rad) < abs(angle_diff_ccw - delta_rad):
                dir_mult = -1  # horario
            else:
                dir_mult = 1   # antihorario
        
        # Generar puntos en orden correcto (de inicio a fin)
        points = [self.start_point]
        
        for i in range(1, num_points):
            fraction = i / num_points
            angle = start_angle + (dir_mult * delta_rad * fraction)
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            points.append((x, y))
        
        # Agregar punto final
        if self.end_point:
            points.append(self.end_point)
        else:
            # Calcular punto final
            final_angle = start_angle + (dir_mult * delta_rad)
            ex = cx + self.radius * math.cos(final_angle)
            ey = cy + self.radius * math.sin(final_angle)
            points.append((ex, ey))
        
        return points
    
    def validate(self) -> Tuple[bool, str]:
        """
        Valida que los parámetros sean geométricamente consistentes.
        
        Returns:
            (es_válido, mensaje_error)
        """
        if not all([self.start_point, self.center, self.radius]):
            return False, "Faltan parámetros requeridos (start_point, center, radius)"
        
        # Verificar que start_point esté aproximadamente a 'radius' del center
        sx, sy = self.start_point
        cx, cy = self.center
        dist_start = math.hypot(sx - cx, sy - cy)
        
        tolerance = max(0.01, self.radius * 0.001)  # 1cm o 0.1% del radio
        if abs(dist_start - self.radius) > tolerance:
            return False, f"Punto inicial no está a la distancia del radio (dist={dist_start:.3f}m, radio={self.radius:.3f}m)"
        
        # Si hay end_point, verificar también
        if self.end_point:
            ex, ey = self.end_point
            dist_end = math.hypot(ex - cx, ey - cy)
            if abs(dist_end - self.radius) > tolerance:
                return False, f"Punto final no está a la distancia del radio (dist={dist_end:.3f}m, radio={self.radius:.3f}m)"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Serializa el segmento curvo a diccionario."""
        return {
            "start_point": self.start_point,
            "end_point": self.end_point,
            "center": self.center,
            "delta": self._delta_str,
            "delta_degrees": self.delta_degrees,
            "radius": self.radius,
            "clockwise": self.clockwise
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CurveSegment':
        """Deserializa desde diccionario."""
        return cls(
            start_point=tuple(data["start_point"]),
            end_point=tuple(data["end_point"]) if data.get("end_point") else None,
            center=tuple(data["center"]),
            delta=data["delta"],
            radius=data["radius"],
            clockwise=data.get("clockwise", True)  # Default True for backwards compatibility
        )
