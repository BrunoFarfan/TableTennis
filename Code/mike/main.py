import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador


# Funciones para enviar datos al Arduino y Faulhabers

def enviar_angulo(manual=False, single=False, angulo=0):
    while loop:
        if not manual:
            angulo = video.generar_angulo()
        comunicador.enviar_angulo(angulo)
    
    # Enviar un solo mensaje
    if single:
        comunicador.enviar_angulo(angulo)

def enviar_velocidad(max_speed=30000):
    while loop:
        velocidades = input("Velocidades: ")
        velocidades = velocidades.split(",")
        try:
            velocidades = [max(-max_speed, min(int(velocidad), max_speed)) for velocidad in velocidades]
            comunicador.enviar_velocidad(velocidades)
        except ValueError:
            print("Error: valores incorrectos para las velocidades")


loop = True # variable para controlar loops secundarios de threads

video = Camara(numero_camara=1, rango=np.array([5, 50, 50]), distancia=1.75)

comunicador = Comunicador(puerto_arduino="COM5")

angle_handler = th.Thread(target=enviar_angulo, daemon=True)
angle_handler.start()

speed_handler = th.Thread(target=enviar_velocidad, daemon=True)
speed_handler.start()

video.iniciar() # Loop principal del programa, se rompe apretando 'q'

loop = False

enviar_angulo(manual=True, single=not loop, angulo=0)

comunicador.stop_faulhabers()