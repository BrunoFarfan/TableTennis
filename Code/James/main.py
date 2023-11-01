import numpy as np
import threading as th
from camara import Camara


video = Camara(numero_camara=0, rango=np.array([5, 50, 150]))

handler = th.Thread(target=video.iniciar, daemon=True)

handler.start()

while True:
    if video.original is not None and video.coordenadas is not None:
        ancho = len(video.original[0])
        alto = len(video.original)
        x = video.coordenadas[0]
        y = video.coordenadas[1]
        print(f"Coordenadas (x, y) absolutas y en porcentaje: {x, y}, "
              f"{round(x/ancho * 100, 1), round(y/alto * 100, 1)}%")