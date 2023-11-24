import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador
import keyboard
import random
import time
import json
import os


class Control:
    def __init__(self, dificultad="normal", auto=True):
        self.video = Camara(rango=np.array([5, 50, 50]), distancia=2.31)
        self.comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14201",
                                       puerto_faulhaber2="/dev/cu.usbserial-1D1120",
                                       puerto_faulhaber1="/dev/cu.usbserial-1D1130",
                                       puerto_faulhaber0="/dev/cu.usbserial-1D1140")

        self.angulo = None
        self.angulo_objetivo = self.angulo
        
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True)
        self.shot_handler = th.Thread(target=self.realizar_disparo, daemon=True,
                                      kwargs={"auto": auto})
        self.speed_handler = th.Thread(target=self.enviar_velocidad, daemon=True)

        self.selector_dificultad(dificultad)

    
    def selector_dificultad(self, dificultad):
        with open(os.path.join("Code", "mike", "parametros.json")) as f:
            self.params = json.load(f)
        self.periodo_disparo = self.params["dificultad"][dificultad]["periodo"]
        self.modo_angulo = self.params["dificultad"][dificultad]["modo_angulo"]
        self.dificultad = dificultad


    def start(self):
        self.loop = True # variable para controlar loops secundarios de threads
        self.angle_handler.start()
        self.shot_handler.start()
        self.speed_handler.start()
        self.video.iniciar()
    

    def manage_stop(self):
        self.loop = False
        self.comunicador.stop_faulhabers()
        self.enviar_angulo(single=True, angulo=0)


    def enviar_angulo(self, single=False, angulo=0):
        while self.loop:
            self.angulo = self.video.generar_angulo()
            if self.angulo != None:
                if self.modo_angulo == "directo":
                    self.angulo_objetivo = self.angulo
                elif self.modo_angulo == "invertido":
                    self.angulo_objetivo = -self.angulo
                self.comunicador.enviar_angulo(self.angulo_objetivo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)

    
    def realizar_disparo(self, auto=True, detener_faulhabers=True):
        t_ultimo_disparo = time.time()
        while self.loop:
            if ((auto and time.time() - t_ultimo_disparo >= self.periodo_disparo and self.angulo != None)
            or keyboard.is_pressed('f')):
                t_ultimo_disparo = time.time()
                vels = self.obtener_velocidad(modo="normal")
                self.comunicador.disparar(velocidad=vels, detener=detener_faulhabers)

    
    def obtener_velocidad(self, prob_largo=0.5, variacion=0.1):
        if self.angulo_objetivo < -5:
            lado = "izquierda"
        elif -5 <= self.angulo_objetivo and self.angulo_objetivo <= 5:
            lado = "centro"
        else:
            lado = "derecha"

        if random.random() <= prob_largo:
            largo = "largo"
        else:
            largo = "corto"

        posibles_tiros = self.params["tiros"][largo][lado]

        if self.dificultad == "facil":
            x, y, h = self.spin_input2spin(posibles_tiros[0])
            return self.spin2velocidad(x, y, h)
        elif self.dificultad == "normal":
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


    def enviar_velocidad(self): # Función temporal para mandar velocidades manualmente
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
    control.manage_stop()