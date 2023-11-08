import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador


class Control:
    def __init__(self):
        self.loop = True # variable para controlar loops secundarios de threads
        self.video = Camara(numero_camara=1, rango=np.array([5, 50, 50]), distancia=1.75)
        self.comunicador = Comunicador()
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True)
        self.speed_handler = th.Thread(target=self.enviar_velocidad, daemon=True)


    def start(self):
        self.angle_handler.start()
        self.speed_handler.start()
        self.video.iniciar()

        self.manage_stop()
    

    def manage_stop(self):
        self.loop = False
        self.comunicador.stop_faulhabers()
        self.enviar_angulo(single=not self.loop, angulo=0)


    def enviar_angulo(self, single=False, angulo=0):
        while self.loop:
            angulo = self.video.generar_angulo()
            self.comunicador.enviar_angulo(angulo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)


    def enviar_velocidad(self, max_speed=30000): # Función temporal para mandar velocidades manualmente
        while self.loop:
            velocidades = input("Velocidades: ")
            try:
                velocidades = velocidades.replace(" ", "").split(",")
                velocidades = [max(-max_speed, min(int(velocidad), max_speed)) for velocidad in velocidades]
                self.comunicador.enviar_velocidad(velocidades, espera=0)
            except ValueError:
                print("Error: valores incorrectos para las velocidades")


if __name__ == "__main__":
    control = Control()
    control.start()