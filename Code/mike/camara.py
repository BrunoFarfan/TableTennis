import cv2
import numpy as np
import keyboard
from detector import DetectorColor, DetectorMovimiento


ANCHO_CANCHA = 1.525

class Camara:
    def __init__(self, numero_camara=None, rango=np.array([5, 20, 30]), distancia=2.74,
                 movimiento=False):
        self.coordenadas = None
        self.original = None
        self.movimiento = movimiento

        self.limites = [] # [izquierdo, derecho]
        self.distancia = distancia

        if movimiento:
            self.detector_objetivo = DetectorMovimiento()
        else:
            self.detector_objetivo = DetectorColor(rango)

        if numero_camara is None:
            numero_camara = self.detectar_camara_externa()
        self.video = cv2.VideoCapture(numero_camara)

    
    def detectar_camara_externa(self): # Asume que solo hay 2 cámaras conectadas
        cap = cv2.VideoCapture(0)
        ancho = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        alto = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps == 25 and alto == 960 and ancho == 1280: # Parámetros C270
            cap.release()
            return 0
        cap.release()
        return 1


    def iniciar(self):
        cv2.namedWindow('original')
        cv2.setMouseCallback('original', self.detector_objetivo.mouseClick)

        self.grabar_video()

    
    def grabar_video(self):
        while True:
            ret, self.original = self.video.read()
            self.detector_objetivo.original = self.original

            if keyboard.is_pressed('q'): # Romper el loop cuando se aprieta 'q'
                break

            cv2.waitKey(1)
            cv2.imshow('original', self.original)

            if not self.movimiento:
                if self.detector_objetivo.color is None:
                    continue            

            self.imagen_filtrada, self.limites, self.coordenadas = self.detector_objetivo.filtrar()

            cv2.imshow('filtrada', self.imagen_filtrada)
        
        self.video.release()
        cv2.destroyAllWindows()


    def generar_angulo(self, angulo_limite=45):
        if self.original is not None and self.coordenadas is not None:
            if len(self.limites) < 2:
                limites = [0, len(self.original[0])]
            else:
                limites = self.limites
            x = self.coordenadas[0] - limites[0]
            x = (x / (limites[1] - limites[0])) - 0.5 # Posición relativa al centro (-0.5 hasta 0.5)
            pos_horizontal = x * ANCHO_CANCHA
            angulo = np.arctan(pos_horizontal/self.distancia)
            angulo = np.rad2deg(angulo)
            angulo = min(angulo_limite, max(-angulo_limite, angulo))
            return angulo