import numpy as np
from camara import Camara


video = Camara(numero_camara=1, rango=np.array([5, 20, 30]))

video.iniciar()