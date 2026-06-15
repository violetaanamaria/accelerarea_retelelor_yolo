#!/usr/bin/env python3

import numpy as np
import yaml
import logging
from typing import List, Dict, Optional, Tuple
from enum import Enum
import sys
from pathlib import Path

# Adaugă path-ul pentru a importa din alte module
sys.path.append(str(Path(__file__).parent.parent))
from inference.yolo_inference import Detection


class ObstacleType(Enum):
    """Tipuri de obstacole"""
    PERSON = "person"
    VEHICLE = "vehicle"
    ANIMAL = "animal"
    STATIC = "static"
    TRAFFIC_SIGN = "traffic_sign"
    UNKNOWN = "unknown"


class DangerLevel(Enum):
    """Niveluri de pericol"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Obstacle:
    """Clasă pentru reprezentarea unui obstacol detectat"""
    
    def __init__(self, detection: Detection, obstacle_type: ObstacleType,
                 danger_level: DangerLevel, distance_estimate: float):
        self.detection = detection
        self.type = obstacle_type
        self.danger_level = danger_level
        self.distance_estimate = distance_estimate  # Estimare distanță relativă (0-1)
        self.position = detection.center  # Poziție în imagine
        self.relative_size = detection.area  # Mărime relativă


class ObstacleDetector:
    """
    Clasă pentru detecția și analiza obstacolelor din detecțiile YOLO
    """
    
    def __init__(self, config_path: str = "config/robot_config.yaml"):
        """
        Inițializare detector obstacole
        
        Args:
            config_path: Calea către fișierul de configurare
        """
        self.config = self._load_config(config_path)
        self.detection_config = self.config['detection']
        self.decision_config = self.config['decision']
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ObstacleDetector')
        
        # Configurare ROI (Region of Interest)
        self.roi = self.detection_config['roi']
        
        # Praguri detecție
        self.obstacle_config = self.detection_config['obstacle']
        self.traffic_sign_config = self.detection_config['traffic_sign']
        
        # Mapare clase -> tipuri obstacole (suportă nume COCO cu spații)
        self.class_to_type = {
            'person': ObstacleType.PERSON,
            'bicycle': ObstacleType.VEHICLE,
            'car': ObstacleType.VEHICLE,
            'motorcycle': ObstacleType.VEHICLE,
            'bus': ObstacleType.VEHICLE,
            'truck': ObstacleType.VEHICLE,
            'dog': ObstacleType.ANIMAL,
            'cat': ObstacleType.ANIMAL,
            'stop_sign': ObstacleType.TRAFFIC_SIGN,
            'stop sign': ObstacleType.TRAFFIC_SIGN,
            'traffic_light': ObstacleType.TRAFFIC_SIGN,
            'traffic light': ObstacleType.TRAFFIC_SIGN,
        }
        
        # Prioritizare din config
        self.priority_map = self.decision_config.get('priority', {
            'person': 10,
            'vehicle': 8,
            'animal': 9,
            'static_obstacle': 5,
            'traffic_sign': 7
        })
        
        self.logger.info("ObstacleDetector inițializat")
    
    def _load_config(self, config_path: str) -> dict:
        """Încarcă configurația din fișier YAML"""
        try:
            path = Path(config_path)
            if not path.is_absolute():
                root = Path(__file__).parent.parent.parent
                path = root / config_path
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.getLogger(__name__).error(f"Eroare la încărcarea configurației: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Returnează configurație implicită"""
        return {
            'detection': {
                'roi': {'x_min': 0.1, 'x_max': 0.9, 'y_min': 0.3, 'y_max': 1.0},
                'obstacle': {'min_area': 0.02, 'danger_zone': 0.6, 'critical_zone': 0.8},
                'traffic_sign': {'min_confidence': 0.7, 'recognition_distance': 0.15}
            },
            'decision': {
                'priority': {'person': 10, 'vehicle': 8, 'animal': 9}
            },
            'logging': {'level': 'INFO'}
        }
    
    def detect_obstacles(self, detections: List[Detection], 
                        frame_shape: Tuple[int, int]) -> List[Obstacle]:
        """
        Analizează detecțiile YOLO și identifică obstacole
        
        Args:
            detections: Listă detecții YOLO
            frame_shape: Dimensiunea frame-ului (height, width)
            
        Returns:
            Listă obstacole detectate
        """
        obstacles = []
        frame_height, frame_width = frame_shape
        frame_area = frame_height * frame_width
        
        for detection in detections:
            # Verifică dacă detecția e în ROI
            if not self._is_in_roi(detection, frame_width, frame_height):
                continue
            
            # Determină tipul obstacolului
            obstacle_type = self.class_to_type.get(
                detection.class_name.lower().strip(),
                ObstacleType.UNKNOWN
            )
            
            # Calculează distanța estimată (bazată pe poziție în imagine)
            distance_estimate = self._estimate_distance(detection, frame_height)
            
            # Determină nivelul de pericol
            danger_level = self._calculate_danger_level(
                detection, 
                obstacle_type,
                distance_estimate,
                frame_area
            )
            
            # Creează obiect Obstacle
            obstacle = Obstacle(
                detection=detection,
                obstacle_type=obstacle_type,
                danger_level=danger_level,
                distance_estimate=distance_estimate
            )
            
            obstacles.append(obstacle)
        
        # Sortează după prioritate/pericol
        obstacles.sort(key=lambda x: x.danger_level.value, reverse=True)
        
        self.logger.debug(f"Detectate {len(obstacles)} obstacole")
        return obstacles
    
    def _is_in_roi(self, detection: Detection, frame_width: int, 
                   frame_height: int) -> bool:
        """
        Verifică dacă detecția se află în Region of Interest
        
        Args:
            detection: Detecție YOLO
            frame_width: Lățime frame
            frame_height: Înălțime frame
            
        Returns:
            True dacă e în ROI
        """
        # Normalizare coordonate
        x_center = detection.center[0] / frame_width
        y_center = detection.center[1] / frame_height
        
        return (self.roi['x_min'] <= x_center <= self.roi['x_max'] and
                self.roi['y_min'] <= y_center <= self.roi['y_max'])
    
    def _estimate_distance(self, detection: Detection, frame_height: int) -> float:
        """
        Estimează distanța relativă la obstacol (0=departe, 1=aproape)
        
        Bazat pe:
        - Poziția Y în imagine (jos = aproape)
        - Mărimea bbox
        
        Args:
            detection: Detecție YOLO
            frame_height: Înălțime frame
            
        Returns:
            Distanță estimată (0-1)
        """
        if frame_height == 0:
            return 0.0

        # Poziția Y (normalizată) - obiecte în partea de jos sunt mai aproape
        y_position = detection.bbox[3] / frame_height  # Bottom edge
        
        # Mărime bbox (normalizată)
        bbox_height = (detection.bbox[3] - detection.bbox[1]) / frame_height
        
        # Combinație: poziție și mărime
        # Obiecte mari și jos sunt foarte aproape
        distance_estimate = (y_position * 0.6 + bbox_height * 0.4)
        
        return min(1.0, max(0.0, distance_estimate))
    
    def _calculate_danger_level(self, detection: Detection, 
                                obstacle_type: ObstacleType,
                                distance_estimate: float,
                                frame_area: int) -> DangerLevel:
        """
        Calculează nivelul de pericol al unui obstacol
        
        Args:
            detection: Detecție YOLO
            obstacle_type: Tip obstacol
            distance_estimate: Distanță estimată (0-1)
            frame_area: Aria totală a frame-ului
            
        Returns:
            Nivel de pericol
        """
        if frame_area == 0:
            return DangerLevel.LOW

        # Calculează aria relativă
        relative_area = detection.area / frame_area
        
        # Verifică praguri
        critical_threshold = self.obstacle_config['critical_zone']
        danger_threshold = self.obstacle_config['danger_zone']
        min_area_threshold = self.obstacle_config['min_area']
        
        # Obiect prea mic - ignora
        if relative_area < min_area_threshold:
            return DangerLevel.LOW
        
        # Zona critică
        if distance_estimate >= critical_threshold:
            return DangerLevel.CRITICAL
        
        # Zona de pericol
        if distance_estimate >= danger_threshold:
            # Prioritizare persoane și animale
            if obstacle_type in [ObstacleType.PERSON, ObstacleType.ANIMAL]:
                return DangerLevel.CRITICAL
            return DangerLevel.HIGH
        
        # Distanță medie
        if distance_estimate >= 0.4:
            if obstacle_type == ObstacleType.PERSON:
                return DangerLevel.HIGH
            return DangerLevel.MEDIUM
        
        # Departe
        return DangerLevel.LOW
    
    def detect_traffic_signs(self, obstacles: List[Obstacle]) -> List[Obstacle]:
        """
        Filtrează și returnează semnele de circulație detectate
        
        Args:
            obstacles: Listă obstacole
            
        Returns:
            Listă semne de circulație
        """
        traffic_signs = [
            obs for obs in obstacles 
            if obs.type == ObstacleType.TRAFFIC_SIGN and
            obs.detection.confidence >= self.traffic_sign_config['min_confidence']
        ]
        
        self.logger.debug(f"Detectate {len(traffic_signs)} semne de circulație")
        return traffic_signs
    
    def get_most_dangerous_obstacle(self, obstacles: List[Obstacle]) -> Optional[Obstacle]:
        """
        Returnează cel mai periculos obstacol
        
        Args:
            obstacles: Listă obstacole
            
        Returns:
            Obstacolul cel mai periculos sau None
        """
        if not obstacles:
            return None
        
        # Deja sortate după danger_level în detect_obstacles()
        return obstacles[0]
    
    def visualize_obstacles(self, image: np.ndarray, 
                           obstacles: List[Obstacle]) -> np.ndarray:
        """
        Desenează obstacole pe imagine cu indicatori de pericol
        
        Args:
            image: Imagine input
            obstacles: Listă obstacole
            
        Returns:
            Imagine cu obstacole desenate
        """
        import cv2
        result = image.copy()
        
        for obstacle in obstacles:
            det = obstacle.detection
            
            # Culoare bazată pe nivel pericol
            color = self._get_danger_color(obstacle.danger_level)
            thickness = 3 if obstacle.danger_level.value >= DangerLevel.HIGH.value else 2
            
            # Desenează bbox
            cv2.rectangle(result, (det.bbox[0], det.bbox[1]), 
                         (det.bbox[2], det.bbox[3]), color, thickness)
            
            # Label cu info
            label = f"{det.class_name} [{obstacle.danger_level.name}]"
            distance_text = f"Dist: {obstacle.distance_estimate:.2f}"
            
            # Background pentru text
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(result, (det.bbox[0], det.bbox[1] - label_size[1] - 25),
                         (det.bbox[0] + max(label_size[0], 100), det.bbox[1]), color, -1)
            
            # Text
            cv2.putText(result, label, (det.bbox[0] + 2, det.bbox[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(result, distance_text, (det.bbox[0] + 2, det.bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return result
    
    def _get_danger_color(self, danger_level: DangerLevel) -> Tuple[int, int, int]:
        """Returnează culoarea pentru nivel de pericol"""
        colors = {
            DangerLevel.NONE: (0, 255, 0),      # Verde
            DangerLevel.LOW: (0, 255, 255),     # Galben
            DangerLevel.MEDIUM: (0, 165, 255),  # Portocaliu
            DangerLevel.HIGH: (0, 0, 255),      # Roșu
            DangerLevel.CRITICAL: (255, 0, 255) # Magenta
        }
        return colors.get(danger_level, (128, 128, 128))


def main():
    """Funcție de test"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('ObstacleDetector_Test')
    
    detector = ObstacleDetector()
    logger.info("ObstacleDetector test complet")


if __name__ == "__main__":
    main()

