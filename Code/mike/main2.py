import cv2
import numpy as np
from detector import DetectorMovimientoColor2
from camara import Camara


# para testear detector de movimiento y color 2:

camara = Camara(numero_camara=0, rango=np.array([5, 50, 50]), distancia=2.31, modo_detector="MovColor")
camara.iniciar()