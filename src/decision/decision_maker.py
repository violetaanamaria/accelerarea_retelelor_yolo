#!/usr/bin/env python3

import yaml
import logging
import time
from typing import List, Optional, Dict
from enum import Enum
import sys
from pathlib import Path

# Adaugă path-ul pentru a importa din alte module
sys.path.append(str(Path(__file__).parent.parent))
from detection.obstacle_detector import Obstacle, ObstacleType, DangerLevel


class RobotAction(Enum):
    """Acțiuni posibile ale robotului"""
    CONTINUE = "continue"          # Continuă înainte
    SLOW_DOWN = "slow_down"        # Reducere viteză
    STOP = "stop"                  # Oprire
    TURN_LEFT = "turn_left"        # Virează stânga
    TURN_RIGHT = "turn_right"      # Virează dreapta
    REVERSE = "reverse"            # Mers înapoi
    EMERGENCY_STOP = "emergency_stop"  # Oprire de urgență


class Decision:
    """Clasă pentru reprezentarea unei decizii"""
    
    def __init__(self, action: RobotAction, speed: float, 
                 reason: str, confidence: float = 1.0):
        self.action = action
        self.speed = speed  # 0-1 (0 = stop, 1 = max speed)
        self.reason = reason
        self.confidence = confidence
        self.timestamp = time.time()


class DecisionMaker:
    """
    Clasă pentru luarea deciziilor bazate pe obstacole detectate
    """
    
    def __init__(self, config_path: str = "config/robot_config.yaml"):
        """
        Inițializare modul decizie
        
        Args:
            config_path: Calea către fișierul de configurare
        """
        self.config = self._load_config(config_path)
        self.decision_config = self.config['decision']
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('DecisionMaker')
        
        # Strategia de evitare și profil de risc (conservative / balanced / aggressive)
        self.avoidance_strategy = self.decision_config.get(
            'avoidance_strategy',
            'stop_and_plan'
        )
        self.risk_profile = self.decision_config.get('risk_profile', 'balanced')
        
        # Timpi de reacție
        self.reaction_time = self.decision_config.get('reaction_time', 100) / 1000.0  # sec
        self.last_decision_time = 0
        
        # Stare curentă
        self.current_action = RobotAction.CONTINUE
        self.stop_start_time = None
        self.stop_duration = self.decision_config.get('stop_duration', 2000) / 1000.0  # sec
        
        # Distanțe de siguranță
        self.safe_distance = self.decision_config['safe_distance']
        
        self.logger.info(
            f"DecisionMaker inițializat: strategie={self.avoidance_strategy}, "
            f"risk_profile={self.risk_profile}"
        )
    
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
            'decision': {
                'avoidance_strategy': 'stop_and_plan',
                'reaction_time': 100,
                'stop_duration': 2000,
                'safe_distance': {'min': 0.3, 'comfortable': 0.5}
            },
            'logging': {'level': 'INFO'}
        }
    
    def make_decision(self, obstacles: List[Obstacle],
                     traffic_signs: List[Obstacle],
                     frame_width: int = 640) -> Decision:
        """
        Ia decizia bazată pe obstacole și semne de circulație
        
        Args:
            obstacles: Listă obstacole detectate
            traffic_signs: Listă semne de circulație
            
        Returns:
            Decizie
        """
        current_time = time.time()
        
        # Verifică timpul de reacție minim
        if current_time - self.last_decision_time < self.reaction_time:
            # Menține decizia anterioară
            return Decision(
                action=self.current_action,
                speed=self._get_speed_for_action(self.current_action),
                reason="Menținere decizie anterioară (reaction time)"
            )
        
        self.last_decision_time = current_time
        
        # 1. Verifică semne de circulație (prioritate înaltă)
        sign_decision = self._check_traffic_signs(traffic_signs)
        if sign_decision:
            self.current_action = sign_decision.action
            return sign_decision
        
        # 2. Verifică dacă suntem în stop temporar (la STOP sign)
        if self.current_action == RobotAction.STOP and self.stop_start_time:
            elapsed = current_time - self.stop_start_time
            if elapsed < self.stop_duration:
                return Decision(
                    action=RobotAction.STOP,
                    speed=0.0,
                    reason=f"Oprire la semn STOP ({elapsed:.1f}s/{self.stop_duration:.1f}s)"
                )
            else:
                # Durata de stop s-a terminat
                self.stop_start_time = None
        
        # 3. Analizează obstacole
        if not obstacles:
            # Niciun obstacol - continuă normal
            self.current_action = RobotAction.CONTINUE
            return Decision(
                action=RobotAction.CONTINUE,
                speed=1.0,
                reason="Drum liber, niciun obstacol detectat"
            )
        
        # Obține cel mai periculos obstacol
        most_dangerous = obstacles[0]  # Deja sortate după pericol
        
        # 4. Decizie bazată pe nivel pericol
        decision = self._decide_based_on_danger(most_dangerous, obstacles, frame_width)
        self.current_action = decision.action
        
        return decision
    
    def _check_traffic_signs(self, traffic_signs: List[Obstacle]) -> Optional[Decision]:
        """
        Verifică semne de circulație și returnează decizie dacă e cazul
        
        Args:
            traffic_signs: Listă semne de circulație
            
        Returns:
            Decizie sau None
        """
        if not traffic_signs:
            return None
        
        for sign in traffic_signs:
            sign_name = sign.detection.class_name.lower()
            
            # STOP sign
            if 'stop' in sign_name:
                if self.stop_start_time is None:
                    self.stop_start_time = time.time()
                
                return Decision(
                    action=RobotAction.STOP,
                    speed=0.0,
                    reason=f"Semn STOP detectat (conf: {sign.detection.confidence:.2f})",
                    confidence=sign.detection.confidence
                )
            
            # Speed limit signs
            if 'speed' in sign_name or 'limit' in sign_name:
                # Reducere viteză
                return Decision(
                    action=RobotAction.SLOW_DOWN,
                    speed=0.5,
                    reason=f"Limitare viteză: {sign_name}",
                    confidence=sign.detection.confidence
                )
            
            # No entry
            if 'no_entry' in sign_name:
                return Decision(
                    action=RobotAction.STOP,
                    speed=0.0,
                    reason="Semn INTRARE INTERZISĂ",
                    confidence=sign.detection.confidence
                )
            
            # Yield
            if 'yield' in sign_name:
                return Decision(
                    action=RobotAction.SLOW_DOWN,
                    speed=0.3,
                    reason="Semn CEDEAZĂ TRECEREA",
                    confidence=sign.detection.confidence
                )
        
        return None
    
    def _decide_based_on_danger(self, primary_obstacle: Obstacle,
                                all_obstacles: List[Obstacle],
                                frame_width: int = 640) -> Decision:
        """
        Ia decizie bazată pe nivelul de pericol al obstacolelor
        
        Args:
            primary_obstacle: Obstacolul principal (cel mai periculos)
            all_obstacles: Toate obstacolele
            
        Returns:
            Decizie
        """
        danger = primary_obstacle.danger_level
        distance = primary_obstacle.distance_estimate
        obstacle_type = primary_obstacle.type
        
        # CRITICAL - oprire imediată
        if danger == DangerLevel.CRITICAL:
            return Decision(
                action=RobotAction.EMERGENCY_STOP,
                speed=0.0,
                reason=f"PERICOL CRITIC: {obstacle_type.value} la distanță {distance:.2f}",
                confidence=1.0
            )
        
        # HIGH - oprire, evitare sau reducere viteză (în funcție de profil)
        if danger == DangerLevel.HIGH:
            if self.risk_profile == 'aggressive':
                return Decision(
                    action=RobotAction.SLOW_DOWN,
                    speed=0.5,
                    reason=f"Pericol înalt ({self.risk_profile}): {obstacle_type.value}, reducere viteză"
                )
            if self.avoidance_strategy == 'swerve' and self.risk_profile != 'conservative':
                avoid_direction = self._calculate_avoidance_direction(
                    primary_obstacle,
                    all_obstacles,
                    frame_width,
                )
                return Decision(
                    action=avoid_direction,
                    speed=0.4,
                    reason=f"Evitare {obstacle_type.value} prin {avoid_direction.value}"
                )
            return Decision(
                action=RobotAction.STOP,
                speed=0.0,
                reason=f"Pericol înalt ({self.risk_profile}): {obstacle_type.value}, oprire preventivă"
            )

        # MEDIUM - reducere viteză (conservative/balanced) sau precauție ușoară (aggressive)
        if danger == DangerLevel.MEDIUM:
            if self.risk_profile == 'aggressive':
                return Decision(
                    action=RobotAction.CONTINUE,
                    speed=0.8,
                    reason=f"Obstacol mediu ({self.risk_profile}): {obstacle_type.value}, precauție"
                )
            speed = 0.4 if self.risk_profile == 'conservative' else 0.6
            return Decision(
                action=RobotAction.SLOW_DOWN,
                speed=speed,
                reason=f"Obstacol la distanță medie ({self.risk_profile}): {obstacle_type.value}"
            )
        
        # LOW - viteză redusă de precauție
        if danger == DangerLevel.LOW:
            return Decision(
                action=RobotAction.CONTINUE,
                speed=0.8,
                reason=f"Obstacol îndepărtat: {obstacle_type.value}, precauție"
            )
        
        # Default - continuă
        return Decision(
            action=RobotAction.CONTINUE,
            speed=1.0,
            reason="Condiții normale de mers"
        )
    
    def _calculate_avoidance_direction(self, primary_obstacle: Obstacle,
                                      all_obstacles: List[Obstacle],
                                      frame_width: int = 640) -> RobotAction:
        """
        Calculează direcția optimă de evitare

        Args:
            primary_obstacle: Obstacol principal
            all_obstacles: Toate obstacolele
            frame_width: Lățimea frame-ului în pixeli

        Returns:
            Acțiune (TURN_LEFT sau TURN_RIGHT)
        """
        obstacle_x = primary_obstacle.position[0]
        if obstacle_x < frame_width // 2:
            return RobotAction.TURN_RIGHT
        else:
            return RobotAction.TURN_LEFT
    
    def _get_speed_for_action(self, action: RobotAction) -> float:
        """
        Returnează viteza normalizată pentru o acțiune
        
        Args:
            action: Acțiune robot
            
        Returns:
            Viteză (0-1)
        """
        speed_map = {
            RobotAction.CONTINUE: 1.0,
            RobotAction.SLOW_DOWN: 0.5,
            RobotAction.STOP: 0.0,
            RobotAction.EMERGENCY_STOP: 0.0,
            RobotAction.TURN_LEFT: 0.6,
            RobotAction.TURN_RIGHT: 0.6,
            RobotAction.REVERSE: 0.4
        }
        return speed_map.get(action, 0.5)
    
    def reset_state(self):
        """Resetează starea internă a decision maker-ului"""
        self.current_action = RobotAction.CONTINUE
        self.stop_start_time = None
        self.last_decision_time = 0
        self.logger.info("Stare decision maker resetată")


def main():
    """Funcție de test"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('DecisionMaker_Test')
    
    decision_maker = DecisionMaker()
    logger.info("DecisionMaker test complet")


if __name__ == "__main__":
    main()

