import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador
import keyboard
import random
import time
import json
import os
import re


class Control:
    def __init__(self, dificultad="normal", auto=True):
        self.video = Camara(rango=np.array([5, 50, 50]), distancia=2.31)
        self.comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14201",
                                       puerto_faulhaber2="/dev/cu.usbserial-1D1120",
                                       puerto_faulhaber1="/dev/cu.usbserial-1D1130",
                                       puerto_faulhaber0="/dev/cu.usbserial-1D1140")

        self.angulo = None
        self.angulo_objetivo = 0
        self.auto = auto
        print("Modo auto: ", auto)
        
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True)
        self.shot_handler = th.Thread(target=self.realizar_disparo, daemon=True)
        self.general_input_handler = th.Thread(target=self.inputs_generales, daemon=True)

        self.selector_dificultad(dificultad)


    def inputs_generales(self):
        while self.loop:
            if keyboard.is_pressed('m'):
                self.auto = False
                print("Modo manual")
                self.comunicador.enviar_velocidad([0, 0, 0])
            elif keyboard.is_pressed('a'):
                self.auto = True
                print("Modo automatico")

            elif keyboard.is_pressed('e'):
                self.selector_dificultad("facil")
            elif keyboard.is_pressed('n'):
                self.selector_dificultad("normal")
            elif keyboard.is_pressed('h'):
                self.selector_dificultad("dificil")

    
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
        self.general_input_handler.start()
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
                elif self.modo_angulo == "esquinado":
                    if np.abs(self.angulo - self.angulo_objetivo) < 7.5 and self.angulo < 0:
                        self.angulo_objetivo = 15
                    elif np.abs(self.angulo - self.angulo_objetivo) < 7.5 and self.angulo > 0:
                        self.angulo_objetivo = -15
                self.comunicador.enviar_angulo(self.angulo_objetivo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)

    
    def obtener_velocidad(self, prob_largo=2/3, variacion=0.1):
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

        elif self.dificultad == "normal" or self.dificultad == "dificil":
            x, y, h = self.spin_input2spin(random.choice(posibles_tiros))
            x += x * random.uniform(-variacion, variacion)
            y += y * random.uniform(-variacion, variacion)
            return self.spin2velocidad(x, y, h)

    
    def spin_input2spin(self, string):
        string = re.sub(r'[vV ]', '', string).lower().split(',')

        if len(string) > 1:
            x, y, h = string[0], string[1].replace("h", ""), "h" in string[1]
        else:
            x, y, h = string[0], 0, False

        x, y = float(x), float(y)
        return (x, y, h)

    
    def spin2velocidad(self, x, y=0, h=False, max_speed=15000):
        if h:
            r1 = x
            r2 = (3 * x + np.sqrt(3) * x  * y)/3
            r3 = (3 * x - np.sqrt(3) * x  * y)/3
        else:
            r1 = (3 * x + 2 * x * y)/3
            r2 = (3 * x - x * y)/3
            r3 = (3 * x - x * y)/3

        velocidades = [round(r1), round(r2), round(r3)]
        velocidades = [max(200, min(velocidad, max_speed)) for velocidad in velocidades]
        return velocidades


    def enviar_velocidad(self): # Función mandar velocidades manualmente y ejecutar un disparo
        spin_input = input("Velocidad (x,yh): ")
        try:
            x, y, h = self.spin_input2spin(spin_input)

            velocidades = self.spin2velocidad(x, y, h)
            self.comunicador.disparar(velocidades)
        except ValueError:
            print("Error: valores incorrectos para las velocidades")

    
    def realizar_disparo(self):
        t_ultimo_disparo = time.time()
        while self.loop:
            diff_tiempo = time.time() - t_ultimo_disparo

            if ((self.auto and diff_tiempo >= self.periodo_disparo and self.angulo != None)
            or keyboard.is_pressed('f')):
                t_ultimo_disparo = time.time()
                print("Disparando")
                vels = self.obtener_velocidad()
                self.comunicador.disparar(velocidad=vels, detener=not self.auto)

            elif keyboard.is_pressed('v'):
                self.enviar_velocidad()



if __name__ == "__main__":
    control = Control(dificultad="dificil")
    control.start()
    control.manage_stop()