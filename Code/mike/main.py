import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador
import keyboard


class Control:
    def __init__(self):
        self.loop = True # variable para controlar loops secundarios de threads
        self.video = Camara(rango=np.array([5, 50, 50]), distancia=2.31, movimiento=False)
        self.comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14201",
                                       puerto_faulhaber2="/dev/cu.usbserial-1D1120",
                                       puerto_faulhaber1="/dev/cu.usbserial-1D1130",
                                       puerto_faulhaber0="/dev/cu.usbserial-1D1140")
        
        self.angle_handler = th.Thread(target=self.enviar_angulo, daemon=True)
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


    def enviar_angulo(self, single=False, angulo=0):
        while self.loop:
            angulo = self.video.generar_angulo()
            if angulo != None:
                self.comunicador.enviar_angulo(angulo)
        
        # Enviar un solo mensaje
        if single:
            self.comunicador.enviar_angulo(angulo)

    
    # 21 porque creo que eso corresponde a 1 grado en el ángulo del pololu
    def realizar_disparo(self, tolerancia=21):
        while self.loop:
            error_angulo = self.comunicador.leer_error_angulo()
            if error_angulo == None:
                continue
            #if error_angulo <= tolerancia or keyboard.is_pressed('f'):
            if keyboard.is_pressed('f'):
                vels = self.obtener_velocidad()
                self.comunicador.disparar(velocidad=vels)

    
    # esta wea tiene que obtener la velocidad de algun dict o algo asi para no tener que darlas
    # manualmente
    def obtener_velocidad(self):
        return self.spin2velocidad(x=12500)

    
    def spin2velocidad(self, x, y=0, h=False):
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
                velocidades = [max(-max_speed, min(velocidad, max_speed)) for velocidad in velocidades]
                self.comunicador.disparar(velocidades) # CAMBIADO A comunicador.disparar PARA QUE DISPARE SOLO LUEGO DE ENVIARLE LAS VELOCIDADES MANUALMENTE
            except ValueError:
                print("Error: valores incorrectos para las velocidades")


if __name__ == "__main__":
    control = Control()
    control.start()