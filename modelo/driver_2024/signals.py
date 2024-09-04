import logging
import time
from blinkstick import blinkstick
from luces import *

class Signal(object):

    def play(self, car):
        pass

    @staticmethod
    def esta_cerca(signal_detected):
        signal_detected_height = (signal_detected[2][3] - signal_detected[2][1]) * 100
        
        return signal_detected_height / 320 > 0


class Stop(Signal):

    def play(self, car):   
        speed = car.back_wheels._speed
        if(speed > 0):
            logging.debug('Haciendo STOP...')
            
            car.keep_following = False
            car.back_wheels.speed = 0

            time.sleep(3)
            
            car.back_wheels.speed = speed
            car.keep_following = True
        
        
class Velocity(Signal):

    def __init__(self, vel):
        self.vel = vel

    def play(self, car):
        logging.debug(f"Ajustando velocidad límite {self.vel}...")
        
        self.keep_following = True
        car.back_wheels.speed = self.vel
        
        
class Ceda(Signal):

    def play(self, car):   
        if(car.back_wheels._speed > 0):
            logging.debug('Haciendo CEDA...')
            
            self.keep_following = True
            car.back_wheels.speed = 20
        
            time.sleep(3)
        
            car.back_wheels.speed = 30

                
class Luces(Signal):

    def play(self, car):    
        logging.debug('Encendiendo LUCES...')
        bstick = blinkstick.find_first()

        if bstick:
            if(not car.lights):
                for i in range(4):
                    bstick.set_color(channel=0, index=i, name="white")
                car.lights = True
            else:
                for i in range(4):
                    bstick.set_color(channel=0, index=i, name="black")
                car.lights = False
        

class Obras(Signal):

    def play(self, car):    
        if(car.back_wheels._speed > 0):
            logging.debug('Conduciendo con precaución por OBRAS...')
            
            self.keep_following = True
            car.back_wheels.speed = 10

            time.sleep(5)
            
            car.back_wheels.speed = 20     
        

class Recto(Signal):

    def play(self, car):    
        if(car.back_wheels._speed > 0):
            logging.debug('Yendo RECTO...')
            
            car.keep_following = False
            car.front_wheels.turn(car.STRAIGHT_ANGLE)
            
            # En 10 segundos recorre 1 metro con una velocidad de 20
            t = 10 
            v = 20

            actual_vel = car.back_wheels._speed
            tiempo = (t * v) / actual_vel
            time.sleep(tiempo)
            
            car.keep_following = True
  
        
class Izquierda(Signal):

    def intermitentes(self, final):
        bstick = blinkstick.find_first()
        while(time.time() < final):
                bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=2, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=3, red=255, green=41, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=2, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=3, red=255, green=41, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=1, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=2, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=3, red=255, green=41, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=1, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=2, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=3, red=255, green=41, blue=0)
                time.sleep(0.3)
                bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=2, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=3, red=0, green=0, blue=0)
                time.sleep(0.2)
        
        for i in range(4):
            bstick.set_color(channel=0, index=i, name="black")

    def play(self, car):    
        actual_vel = car.back_wheels._speed
        if(actual_vel > 0):
            logging.debug('Yendo a la IZQUIERDA...')
            start = time.time()
            
            # En 10 segundos recorre 1 metro con una velocidad de 20
            t = 10 
            v = 20
            
            duration = (t * v) / actual_vel
            
            final = start + duration
            
            car.keep_following = False
            car.front_wheels.turn(80)
            car.front_wheels.turn(70)
            car.front_wheels.turn(60)
            car.front_wheels.turn(50)
            car.front_wheels.turn(45)
            
            self.intermitentes(final)

            car.front_wheels.turn(car.STRAIGHT_ANGLE)
            car.keep_following = True
        
        else:  self.intermitentes(time.time() + 5)
        
        
        
class Derecha(Signal):

    def intermitentes(self, final):
        bstick = blinkstick.find_first()
        while(time.time() < final):
                bstick.set_color(channel=0, index=0, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=2, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=3, red=0, green=0, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=1, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=2, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=3, red=0, green=0, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=1, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=2, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=3, red=0, green=0, blue=0)
                time.sleep(0.2)
                bstick.set_color(channel=0, index=0, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=1, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=2, red=255, green=41, blue=0)
                bstick.set_color(channel=0, index=3, red=255, green=41, blue=0)
                time.sleep(0.3)
                bstick.set_color(channel=0, index=0, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=1, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=2, red=0, green=0, blue=0)
                bstick.set_color(channel=0, index=3, red=0, green=0, blue=0)
                time.sleep(0.2)
                
        for i in range(4):
            bstick.set_color(channel=0, index=i, name="black")
        
    def play(self, car):   
        actual_vel = car.back_wheels._speed 
        if(actual_vel > 0):
            logging.debug('Yendo a la DERECHA...')      
            start = time.time()
            
            # En 10 segundos recorre 1 metro con una velocidad de 20
            t = 10 
            v = 20
            duration = (t * v) / actual_vel
            
            final = start + duration
            
            car.keep_following = False
            car.front_wheels.turn(100)
            car.front_wheels.turn(110)
            car.front_wheels.turn(120)
            car.front_wheels.turn(130)
            car.front_wheels.turn(135)
            
            self.intermitentes(final)
            
            car.front_wheels.turn(car.STRAIGHT_ANGLE)
            car.keep_following = True
        
        else: self.intermitentes(time.time() + 5)
            
        
                     
class Rojo(Signal):

    def play(self, car):
        logging.debug('Parando por SEMÁFORO ROJO...')
        
        car.keep_following = False
        car.back_wheels.speed = 0
        
        time.sleep(3)
        
        
class Verde(Signal):

    def play(self, car):
        logging.debug('Continuando conducción por SEMÁFORO VERDE...')      
        vel = car.back_wheels._speed
        
        if(vel==0):
            car.back_wheels.speed = 20
            
        car.keep_following = True