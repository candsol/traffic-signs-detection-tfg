#------------------------------------------------------------------------------
# El programa crea una clase LaneFollower,
# la cual calcula el ángulo de giro del coche para una imagen de entrada
# utilizando un modelo de aprendizaje profundo compilado en formato .tflite.
#------------------------------------------------------------------------------

import cv2
import numpy as np
import logging
import math
import time
from pycoral.utils import edgetpu
from pycoral.adapters import common
from signals import *

class LaneFollower(object):

    def __init__(self,
                 car=None,
                 model_path='/home/pi/Smart-Pi-Car/models/lane-navigation-model-finetuned.tflite'):
        logging.info('Poniendo a punto el procesador (LaneFollower)')

        self.car = car
        self.curr_steering_angle = 90
        
        # Inicializa el intérprete de Tensorflow
        self.interpreter = edgetpu.make_interpreter(model_path)
        self.interpreter.allocate_tensors()


    def follow_lane(self, frame):
        ''' Método principal de la clase, llama a los demás '''

        new_steering_angle = self.compute_steering_angle(frame)
        self.curr_steering_angle = self.stabilize_steering_angle(new_steering_angle)
        logging.debug(f"Ángulo de giro: {self.curr_steering_angle} grados")

        if self.car is not None:
            self.car.front_wheels.turn(self.curr_steering_angle)
        final_frame = display_heading_line(frame, self.curr_steering_angle)

        return final_frame


    def stabilize_steering_angle(self, new_steering_angle):
        ''' Acota el ángulo de giro a un máximo de 3 grados respecto al anterior '''

        stabilized_steering_angle = new_steering_angle
        max_angle_deviation = 3
        angle_deviation = new_steering_angle - self.curr_steering_angle
        if angle_deviation > max_angle_deviation:
            stabilized_steering_angle = self.curr_steering_angle + max_angle_deviation
        elif angle_deviation < -max_angle_deviation:
            stabilized_steering_angle = self.curr_steering_angle - max_angle_deviation
        return stabilized_steering_angle
            

    def compute_steering_angle(self, frame):
        ''' Calcula el ángulo de giro mediante el modelo '''
        
        input_frame = img_preprocess(frame)
        common.set_input(self.interpreter, input_frame)

        output_details = self.interpreter.get_output_details()[0]
        
        #start = time.time()
        self.interpreter.invoke()
        #end = time.time()
        
        #logging.info(end-start)
        steering_angle = self.interpreter.get_tensor(output_details['index'])

        steering_angle = int(steering_angle + 0.5) # redondeo
        return steering_angle


class TrafficSignDetector(object):
    
    def __init__(self,
                    car=None,
                    model_path='/home/pi/Smart-Pi-Car_2024/models/ultimo.tflite'):
        
        logging.info('Poniendo a punto el procesador (TrafficSignDetector)')
        
        self.car = car
        self.threshold = 0.6
                                
        self.traffic_objects = {0: Stop(),
                                1: Velocity(30),
                                2: Velocity(60),
                                3: Ceda(),
                                4: Luces(),
                                5: Obras(),
                                6: Recto(),
                                7: Izquierda(),
                                8: Derecha(),
                                9: Verde(),
                                10: Rojo()}                     
        
        # Inicializa el intérprete de Tensorflow
        self.interpreter = edgetpu.make_interpreter(model_path)
        
        self.interpreter.allocate_tensors()
        
        with open('/home/pi/Smart-Pi-Car_2024/models/labelmap.txt', 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
  
        
    def detect_signal(self, frame):
        input_frame = img_preprocess(frame, signal = True)
        common.set_input(self.interpreter, input_frame)
        
        output_details = self.interpreter.get_output_details()
        #start = time.time()
        self.interpreter.invoke()
        #end = time.time()
        #logging.info(end-start)

        boxes = self.interpreter.get_tensor(output_details[1]['index'])[0]
        classes = self.interpreter.get_tensor(output_details[3]['index'])[0]
        scores = self.interpreter.get_tensor(output_details[0]['index'])[0]
        
        detections = []

        for i in range(len(scores)):
            if ((scores[i] > self.threshold)):  
                object_name = self.labels[int(classes[i])] 
                detections.append([object_name, scores[i], boxes[i], int(classes[i])])
                
        signal_detected = 'Nada'   
        
        if(len(detections)>0):
            signal_detected = detections[0][0]
            logging.debug(signal_detected)
            logging.debug(detections[0])
            
            signal = self.traffic_objects[int(detections[0][3])]

            if signal.esta_cerca(detections[0]):
                logging.debug('La señal está cerca, interpretándola...')
                signal.play(self.car)
            else:
                logging.debug('Se detectó la señal, pero está demasiado lejos, ignorándola...')
        
        return signal_detected                       

def img_preprocess(image, signal=False):
    ''' Ajusta el fotograma a la entrada del modelo '''

    if(signal):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (320, 320))
        image = np.expand_dims(image, axis=0)
    else:
        height = len(image)
        image = image[int(height/2):,:,:]
        image = cv2.resize(image, (200,66))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image / 255
        
    return image


def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5):
    ''' Muestra por pantalla una línea en la dirección a la que se dirije el coche '''
    
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
