import numpy as np
import threading as th
from camara import Camara
from comm import Comunicador


def enviar_angulo():
    while True:
        angulo = video.generar_angulo()
        comunicador.enviar_angulo(angulo)
        print(angulo)


video = Camara(numero_camara=1, rango=np.array([5, 50, 50]))

comunicador = Comunicador()

comm_handler = th.Thread(target=enviar_angulo, daemon=True)
comm_handler.start()

video.iniciar()