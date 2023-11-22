import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador
import keyboard
from tiros import diccionario_tiros
import random


class Control:
    def __init__(self):
        self.loop = True # variable para controlar loops secundarios de threads
        self.video = Camara(rango=np.array([5, 50, 50]), distancia=2.31)
        self.comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14201",
                                       puerto_faulhaber2="/dev/cu.usbserial-1D1120",
                                       puerto_faulhaber1="/dev/cu.usbserial-1D1130",
                                       puerto_faulhaber0="/dev/cu.usbserial-1D1140")

        self.angulo = None
        
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True,
                                       kwargs={"invertir": True})
        self.shot_handler = th.Thread(target=self.realizar_disparo, daemon=True)
        self.speed_handler = th.Thread(target=self.enviar_velocidad, daemon=True)


    def start(self):
        self.angle_handler.start()
        self.shot_handler.start()
        self.speed_handler.start()
        self.video.iniciar()

        self.manage_stop()
    

    def manage_stop(self):
        self.loop = False
        self.comunicador.stop_faulhabers()
        self.enviar_angulo(single=not self.loop, angulo=0)


    def enviar_angulo(self, single=False, angulo=0, invertir=True):
        while self.loop:
            self.angulo = self.video.generar_angulo()
            if self.angulo != None:
                if invertir:
                    self.angulo = -self.angulo
                self.comunicador.enviar_angulo(self.angulo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)

    
    # 21 porque creo que eso corresponde a 1 grado en el ángulo del pololu
    def realizar_disparo(self, tolerancia=21):
        while self.loop:
            error_angulo = self.comunicador.leer_error_angulo()
            if error_angulo == None or self.angulo == None:
                continue
            if error_angulo <= tolerancia or keyboard.is_pressed('f'):
            # if keyboard.is_pressed('f'):
                vels = self.obtener_velocidad(modo="normal")
                self.comunicador.disparar(velocidad=vels, detener=False)

    
    def obtener_velocidad(self, modo="facil", prob_largo=0.5, variacion=0.1):
        if self.angulo < -5:
            lado = "izquierda"
        elif -5 <= self.angulo and self.angulo <= 5:
            lado = "centro"
        else:
            lado = "derecha"

        if random.random() <= prob_largo:
            largo = "largo"
        else:
            largo = "corto"

        posibles_tiros = diccionario_tiros[largo][lado]

        if modo == "facil":
            x, y, h = self.spin_input2spin(posibles_tiros[0])
            return self.spin2velocidad(x, y, h)
        elif modo == "normal":
            x, y, h = self.spin_input2spin(random.choice(posibles_tiros))
            x += x * random.uniform(-variacion, variacion)
            y += y * random.uniform(-variacion, variacion)
            return self.spin2velocidad(x, y, h)

    
    def spin_input2spin(self, string):
        string = string.replace(" ", "").lower().split(",")

        if len(string) > 1:
            x, y, h = string[0], string[1].replace("h", ""), "h" in string[1]
        else:
            x, y, h = string[0], 0, False

        x, y = float(x), float(y)
        return (x, y, h)

    
    def spin2velocidad(self, x, y=0, h=False, max_speed=30000):
        if h:
            r1 = x
            r2 = (3 * x + np.sqrt(3) * x  * y)/3
            r3 = (3 * x - np.sqrt(3) * x  * y)/3
        else:
            r1 = (3 * x + 2 * x * y)/3
            r2 = (3 * x - x * y)/3
            r3 = (3 * x - x * y)/3

        velocidades = [round(r1), round(r2), round(r3)]
        velocidades = [max(200, min(velocidad, max_speed)) for velocidad in velocidades] # V siempre entre 100 y max
        return velocidades


    def enviar_velocidad(self, max_speed=30000): # Función temporal para mandar velocidades manualmente
        while self.loop:
            spin_input = input("Velocidades (x,yh): ")
            try:
                x, y, h = self.spin_input2spin(spin_input)

                velocidades = self.spin2velocidad(x, y, h)
                self.comunicador.disparar(velocidades) # CAMBIADO A comunicador.disparar PARA QUE DISPARE SOLO LUEGO DE ENVIARLE LAS VELOCIDADES MANUALMENTE
            except ValueError:
                print("Error: valores incorrectos para las velocidades")


if __name__ == "__main__":
    control = Control()
    control.start()