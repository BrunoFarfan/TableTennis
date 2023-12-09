import cv2
import numpy as np
import keyboard
from time import sleep
from detector import DetectorMaestro


ANCHO_CANCHA = 1.525

class Camara:
    def __init__(self, numero_camara= None, distancia= 2.74, modo= 0, rango_color= np.array([5, 20, 30]), rango_cara= (30, 70)):
        
        self.coordenadas = None
        self.original = None
        self.filtrada = None

        self.limites = [] # [izquierdo, derecho]
        self.distancia = distancia

        self.modo = modo
        self.detector_objetivo = DetectorMaestro(modo= modo,
                                                rango_color= rango_color,
                                                max_layers= 5, thresh= 15, kernel= np.ones((5,5), np.uint8),
                                                rango_cara= rango_cara, d_angle= 60, angle_tolerance= 5)

        if numero_camara is None:
            numero_camara = self.detectar_camara_externa()
        self.video = cv2.VideoCapture(numero_camara)

        self.active = False

    
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
        self.active = True
        while self.active:
            ret, self.original = self.video.read()
            self.detector_objetivo.original = self.original

            if keyboard.is_pressed('q'): # Romper el loop cuando se aprieta 'q'
                self.active = False
            if keyboard.is_pressed('m'): # Cambiar de filtro
                cv2.destroyWindow(f'filtrada {self.modo}')
                if self.modo == 3:
                    self.modo = 0
                else:
                    self.modo += 1
                self.detector_objetivo.modo = self.modo
                sleep(0.1)
                
            cv2.waitKey(1)
            cv2.imshow('original', self.original)

            self.filtrada, self.limites, self.coordenadas = self.detector_objetivo.filtrar()

            cv2.imshow(f'filtrada {self.modo}', self.filtrada)
        
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