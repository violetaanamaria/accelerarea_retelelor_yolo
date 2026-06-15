#!/usr/bin/env python3

import cv2
import numpy as np
import yaml
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
import threading
from queue import Queue


class VideoCapture:
    """
    Clasă pentru captura video optimizată cu buffering și threading
    """
    
    def __init__(self, config_path: str = "config/robot_config.yaml"):
        """
        Inițializare modul captura video
        
        Args:
            config_path: Calea către fișierul de configurare
        """
        self.config = self._load_config(config_path)
        self.camera_config = self.config['camera']
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('VideoCapture')
        
        # Inițializare cameră
        self.cap = None
        self.is_running = False
        self.frame_queue = Queue(maxsize=self.config['performance']['buffer_size'])
        self.capture_thread = None
        
        # Statistici
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self._fps_lock = threading.Lock()
        
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
            print(f"Eroare la încărcarea configurației: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Returnează configurație implicită"""
        return {
            'camera': {
                'device': '/dev/video0',
                'width': 640,
                'height': 480,
                'fps': 30,
                'format': 'MJPEG'
            },
            'logging': {'level': 'INFO'},
            'performance': {'buffer_size': 5}
        }
    
    def initialize(self) -> bool:
        """
        Inițializează camera și setează parametrii
        
        Returns:
            True dacă inițializarea a reușit, False altfel
        """
        try:
            self.logger.info(f"Inițializare cameră: {self.camera_config['device']}")
            
            # Deschide camera
            # Pentru Kria KV260 cu camera Raspberry Pi, folosim V4L2
            self.cap = cv2.VideoCapture(self.camera_config['device'], cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                self.logger.error("Nu s-a putut deschide camera!")
                return False
            
            # Setează parametrii cameră
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config['width'])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config['height'])
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_config['fps'])
            
            # Setează format (MJPEG pentru performanță mai bună)
            if self.camera_config['format'] == 'MJPEG':
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Setări opționale
            if 'brightness' in self.camera_config:
                self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_config['brightness'])
            if 'contrast' in self.camera_config:
                self.cap.set(cv2.CAP_PROP_CONTRAST, self.camera_config['contrast'])
            if 'saturation' in self.camera_config:
                self.cap.set(cv2.CAP_PROP_SATURATION, self.camera_config['saturation'])
            
            # Verifică setările
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            self.logger.info(f"Cameră inițializată: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Eroare la inițializarea camerei: {e}")
            return False
    
    def _capture_loop(self):
        """Loop de captură în thread separat pentru performanță optimă"""
        self.logger.info("Thread de captură pornit")
        
        while self.is_running:
            ret, frame = self.cap.read()
            
            if not ret:
                self.logger.warning("Nu s-a putut citi frame-ul de la cameră")
                continue
            
            # Adaugă frame în queue (înlocuiește cel mai vechi dacă e plin)
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
            
            self.frame_queue.put(frame)
            
            # Update FPS
            with self._fps_lock:
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = current_time
        
        self.logger.info("Thread de captură oprit")
    
    def start(self) -> bool:
        """
        Pornește captura video în thread separat
        
        Returns:
            True dacă pornirea a reușit
        """
        if not self.cap or not self.cap.isOpened():
            self.logger.error("Camera nu este inițializată!")
            return False
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        self.logger.info("Captura video pornită")
        return True
    
    def stop(self):
        """Oprește captura video"""
        self.is_running = False

        if getattr(self, 'capture_thread', None):
            self.capture_thread.join(timeout=2.0)

        if getattr(self, 'cap', None):
            self.cap.release()

        if getattr(self, 'logger', None):
            self.logger.info("Captura video oprită")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Citește frame-ul cel mai recent din buffer
        
        Returns:
            Tuple (success, frame)
        """
        if self.frame_queue.empty():
            return False, None
        
        try:
            frame = self.frame_queue.get(timeout=0.1)
            return True, frame
        except:
            return False, None
    
    def get_fps(self) -> float:
        """Returnează FPS-ul curent"""
        with self._fps_lock:
            return self.fps
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Returnează dimensiunea frame-urilor (width, height)"""
        return (self.camera_config['width'], self.camera_config['height'])
    
    def __del__(self):
        """Destructor - cleanup resurse"""
        self.stop()


def main():
    """Funcție de test pentru modulul de captură video"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('VideoCapture_Test')
    
    # Inițializare
    capture = VideoCapture()
    
    if not capture.initialize():
        logger.error("Eșec la inițializarea camerei!")
        return
    
    if not capture.start():
        logger.error("Eșec la pornirea capturii!")
        return
    
    logger.info("Apasă 'q' pentru a ieși")
    
    try:
        while True:
            ret, frame = capture.read()
            
            if ret and frame is not None:
                # Afișează FPS pe imagine
                fps_text = f"FPS: {capture.get_fps():.1f}"
                cv2.putText(frame, fps_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Afișează frame
                cv2.imshow('Video Capture Test', frame)
            
            # Ieșire cu 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        logger.info("Întrerupt de utilizator")
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        logger.info("Test finalizat")


if __name__ == "__main__":
    main()

