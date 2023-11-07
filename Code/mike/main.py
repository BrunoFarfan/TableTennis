import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador


def enviar_angulo(manual=False, single=False, angulo=0):
    while loop:
        if not manual:
            angulo = video.generar_angulo()
        comunicador.enviar_angulo(angulo)
        print(angulo)
    
    # Enviar un solo mensaje
    if single:
        comunicador.enviar_angulo(angulo)
        print(angulo)


loop = True # variable para controlar loops secundarios

video = Camara(numero_camara=1, rango=np.array([5, 50, 50]), distancia=1.75)

comunicador = Comunicador(puerto_arduino="/dev/cu.usbmodem14201")

comm_handler = th.Thread(target=enviar_angulo, daemon=True)
comm_handler.start()

video.iniciar() # Loop principal del programa, se rompe apretando cualquier tecla

loop = False

enviar_angulo(manual=True, single=not loop, angulo=0)