import numpy as np
import threading as th
from camara import Camara


video = Camara(numero_camara=1, rango=np.array([5, 50, 150]))

video.iniciar()