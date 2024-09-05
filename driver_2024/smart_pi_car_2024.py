#------------------------------------------------------------------------------
# El programa inicializa un coche SmartPiCar y lo conduce de la forma escogida por el usuario:
# - Manual: mediante el teclado
# - Auto: mediante el modelo de aprendizaje profundo
# - Entrenamiento manual: manual recopilando imágenes etiquetadas
# - Entrenamiento auto: mediante una programación explícita, guardando un video de la conducción
#------------------------------------------------------------------------------

import logging
import picar
import cv2
import datetime
import sys
import os
import time
import traceback
from autonomous_driver_2024 import LaneFollower, TrafficSignDetector
import threading

#mode = 'auto'

class SmartPiCar(object):

    CAMERA_WIDTH = 320
    CAMERA_HEIGHT = 240
    STRAIGHT_ANGLE = 90

    def __init__(self):
        """ Inicializa el coche y la cámara """
        logging.info("Creando un Smart Pi Car...")

        picar.setup()

        logging.debug("Preparando la cámara...")
        self.camera = cv2.VideoCapture(0)
        self.camera.set(3, self.CAMERA_WIDTH)
        self.camera.set(4, self.CAMERA_HEIGHT)
        
        self.actual_frame = None

        self.horizontal_servo = picar.Servo.Servo(1)
        self.horizontal_servo.offset = 20  # calibra el servo al centro
        self.horizontal_servo.write(self.STRAIGHT_ANGLE)

        self.vertical_servo = picar.Servo.Servo(2)
        self.vertical_servo.offset = 0  # calibra el servo al centro
        self.vertical_servo.write(self.STRAIGHT_ANGLE)
        logging.debug("Cámara lista.")

        logging.debug("Preparando las ruedas...")
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0  # El rango de velocidad es 0 - 100

        self.steering_angle = self.STRAIGHT_ANGLE
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turning_offset = -10  # calibra el servo al centro
        self.front_wheels.turn(self.steering_angle)  # El ángulo de giro es 45 (izquierda) - 90 (recto) - 135 (derecha)
        logging.debug("Ruedas listas.")
        self.keep_following = True
        self.keep_detecting = True
        self.lights = False
        
        self.short_date_str = datetime.datetime.now().strftime("%d%H%M")
        
        self.lane_follower = LaneFollower(self)
        self.traffic_sign_detector = TrafficSignDetector(self)
        
        logging.info("Smart Pi Car creado con éxito.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if traceback is not None:
            self.keep_following = False
            self.keep_detecting = False
            self.back_wheels.speed = 0
            error = traceback.format_exc()
            logging.error(f"Parando la ejecución con el error:\n{error}")

        self.cleanup()

    def cleanup(self):
        """ Resetea el hardware """
        logging.info("Parando el coche, restaurando el hardware...")
        self.back_wheels.speed = 0
        self.front_wheels.turn(self.STRAIGHT_ANGLE)
        self.camera.release()
        
        self.keep_following = False
        self.keep_detecting = False
        
        cv2.destroyAllWindows()
        logging.info("Coche detenido.")
        sys.exit()

    def manual_driver(self):
        """ Conduce mediante las teclas A (derecha) y D (izquierda) """
        pressed_key = cv2.waitKey(50) & 0xFF
        if pressed_key == ord('a'):
            if self.steering_angle > 40: self.steering_angle -= 3
            self.front_wheels.turn(self.steering_angle)
        elif pressed_key == ord('d'):
            if self.steering_angle < 140: self.steering_angle += 3
            self.front_wheels.turn(self.steering_angle)
        elif pressed_key == ord('p'):
            self.keep_following = False
            self.keep_detecting = False
            self.back_wheels.speed = 0 # pausa
        elif pressed_key == ord('g'):
            self.keep_following = True
            self.keep_detecting = True
            self.back_wheels.speed = 20 # go, arranca
        elif pressed_key == ord('t'):
            return True     #take photo
        elif pressed_key == ord('q'):
            self.cleanup()
        
        return False

    def traffic_sign_detection_task(self):
        while self.keep_detecting:
            if(self.actual_frame is not None):
                #start = time.time()
                logging.info('detecting...........................')
                signal = self.traffic_sign_detector.detect_signal(self.actual_frame)
                #end = time.time()
                logging.info(signal)
                #logging.info(end-start)
                time.sleep(2) 
    
    def start_detection_task(self):
        threading.Thread(target=self.traffic_sign_detection_task).start()

    def drive(self, mode='auto', speed=30):
        """ Arranca el coche """
        
        self.back_wheels.speed = speed
        i = 0
        
        if mode == "auto":
            logging.info("Iniciando la conducción autónoma...")
            logging.info(f"Arrancando a una velocidad de {speed}...")
            
            self.start_detection_task()
            
            while self.camera.isOpened():
                _, self.actual_frame = self.camera.read()
                
                image_lane = self.actual_frame
                
                if(self.keep_following):
                    image_lane = self.lane_follower.follow_lane(self.actual_frame)

                cv2.imshow('Video', image_lane)

                pressed_key = cv2.waitKey(1) & 0xFF
                if pressed_key == ord('q'):
                   self.cleanup()
                   break
                elif pressed_key == ord('p'):
                    self.keep_following = False
                    self.keep_detecting = False
                    self.back_wheels.speed = 0
                elif pressed_key == ord('g'):
                    self.keep_following = True
                    self.keep_detecting = True
                    self.start_detection_task()
                    self.back_wheels.speed = speed
        
        elif mode == "entrenamiento_manual": 
            logging.info("Iniciando la conducción manual...")
            logging.info(f"Arrancando a una velocidad de {speed}...")
            os.chdir('../footage')

            while self.camera.isOpened():
                _, self.actual_frame = self.camera.read()
                
                cv2.imshow('Video',self.actual_frame)

                take_photo = self.manual_driver()
                
                if (take_photo==True):
                    cv2.imwrite('v%s-f%03d-a%03d.png' % (self.short_date_str, i, self.steering_angle), self.actual_frame)
                    i += 1 
                    logging.info(f"Frame {i} guardado")
                
                time.sleep(0.2)

        elif mode == "entrenamiento_auto":
            logging.info("Iniciando la conducción autónoma y capturando frames...")
            logging.info(f"Arrancando a una velocidad de {speed}...")

            while self.camera.isOpened():
                
                _, self.actual_frame = self.camera.read()

                image_lane = self.actual_frame
                
                if(self.keep_following):
                    image_lane = self.lane_follower.follow_lane(self.actual_frame)

                cv2.imshow('Video', image_lane)
                
                pressed_key = cv2.waitKey(50) & 0xFF
                if pressed_key == ord('q'):
                    self.cleanup()
                    break
                elif pressed_key == ord('p'):
                    self.keep_following = False
                    self.keep_detecting = False
                    self.back_wheels.speed = 0
                elif pressed_key == ord('g'):
                    self.keep_following = True
                    self.keep_detecting = True
                    self.back_wheels.speed = speed

                cv2.imwrite('v%s-f%03d-a%03d.png' % (self.short_date_str, i, self.steering_angle), self.actual_frame)
                logging.info(f"Frame {i} guardado")
                i += 1
                time.sleep(2)
                 
        else:
            logging.info("Iniciando la conducción manual...")
            logging.info(f"Arrancando a una velocidad de {speed}...")

            while self.camera.isOpened():
                _, self.actual_frame = self.camera.read()

                cv2.imshow('Video', self.actual_frame)

                _ = self.manual_driver()


def main(mode):
    with SmartPiCar() as car:
        car.drive(mode)
            

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(asctime)s: %(message)s')

    if len(sys.argv) > 1:
        if sys.argv[1] not in ['manual', 'entrenamiento_manual','auto', 'entrenamiento_auto']:
            logging.error('Por favor, escriba el modo de conducción deseado después del nombre del programa.\n \
                            - "manual": conducción mediante el teclado\n \
                            - "auto": conducción autónoma mediante inteligencia artificial\n \
                            - "entrenamiento_manual": conducción mediante el teclado recopilando datos\n \
                            - "entrenamiento_auto": conducción autónoma (sin inteligencia artificial) recopilando datos')
            sys.exit()
        else: main(sys.argv[1])

    else: main("auto")