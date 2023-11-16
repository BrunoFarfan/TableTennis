import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador


class Control:
    def __init__(self):
        self.loop = True # variable para controlar loops secundarios de threads
        self.video = Camara(rango=np.array([5, 50, 50]), distancia=1.75)
        self.comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14101",
                                       puerto_faulhaber0="/dev/cu.usbserial-1A1210",
                                       puerto_faulhaber1="/dev/cu.usbserial-1A1220",
                                       puerto_faulhaber2="/dev/cu.usbserial-1A1230")
        
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True)
        self.shot_handler = th.Thread(target=self.disparo_automatico, daemon=True)
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


    def enviar_angulo(self, single=False, angulo=0):
        while self.loop:
            angulo = self.video.generar_angulo()
            if angulo != None:
                self.comunicador.enviar_angulo(angulo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)

    
    # 21 porque creo que eso corresponde a 1 grado en el ángulo del pololu
    def disparo_automatico(self, tolerancia=21):
        while self.loop:
            error_angulo = self.comunicador.leer_error_angulo()
            if error_angulo != None:
                continue
            print(f"Angulo actual: {error_angulo}")
            if error_angulo <= tolerancia:
                print("Disparo!")
                self.comunicador.disparar()

    
    def spin2velocidad(self, x, y, h=False):
        x, y = float(x), float(y)
        if h:
            r1 = x
            r2 = (3 * x + np.sqrt(3) * x  * y)/3
            r3 = (3 * x - np.sqrt(3) * x  * y)/3
        else:
            r1 = (3 * x + 2 * x * y)/3
            r2 = (3 * x - x * y)/3
            r3 = (3 * x - x * y)/3
        return [round(r1), round(r2), round(r3)]


    def enviar_velocidad(self, max_speed=30000): # Función temporal para mandar velocidades manualmente
        while self.loop:
            spin_input = input("Velocidades (x,yh): ")
            try:
                spin_input = spin_input.replace(" ", "").lower().split(",")
                spin_input = spin_input

                if len(spin_input) > 1:
                    x, y, h = spin_input[0], spin_input[1].replace("h", ""), "h" in spin_input[1]
                else:
                    x, y, h = spin_input[0], 0, False

                velocidades = self.spin2velocidad(x, y, h)
                velocidades = [max(0, min(velocidad, max_speed)) for velocidad in velocidades] # Limitar velocidades al intervalo [0, max_speed]
                self.comunicador.enviar_velocidad(velocidades)
            except ValueError:
                print("Error: valores incorrectos para las velocidades")


if __name__ == "__main__":
    control = Control()
    control.start()