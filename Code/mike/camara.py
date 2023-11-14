import cv2
import numpy as np
import keyboard


ANCHO_CANCHA = 1.525

class Camara:
    def __init__(self, numero_camara=None, rango=np.array([5, 20, 30]), distancia=2.74):
        self.rango = rango
        self.color = None
        self.coordenadas = None
        self.ultimas_coordenadas = None
        self.original = None

        self.limites = [] # [izquierdo, derecho]
        self.distancia = distancia

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


    def mouseRGB(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            colorsB = self.original[y, x, 0]
            colorsG = self.original[y, x, 1]
            colorsR = self.original[y, x, 2]
            colors = self.original[y, x]
            hsv_value = np.uint8([[[colorsB, colorsG, colorsR]]])
            hsv = cv2.cvtColor(hsv_value, cv2.COLOR_BGR2HSV)

            if len(self.limites) < 2:
                self.limites.append(x)
            else:
                self.lower_color = hsv - self.rango
                self.upper_color = hsv + self.rango

                self.color = hsv


    def iniciar(self):
        cv2.namedWindow('original')
        cv2.setMouseCallback('original', self.mouseRGB)

        self.grabar_video()


    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.ultimas_coordenadas = np.array([cX, cY])
        else:
            cX, cY = self.ultimas_coordenadas

        cv2.circle(self.imagen_filtrada, (cX, cY), 5, (255, 255, 255), -1)
        cv2.putText(self.imagen_filtrada, "centroid", (cX - 25, cY - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if len(self.limites) == 2:
            izquierdo = self.limites[0]
            derecho = self.limites[1]

            cv2.line(self.imagen_filtrada, np.array([izquierdo, 0]),
                     np.array([izquierdo, len(self.original)]), (255, 255, 255), 3)
            cv2.line(self.imagen_filtrada, np.array([derecho, 0]),
                     np.array([derecho, len(self.original)]), (255, 255, 255), 3)

        self.coordenadas = np.array([cX, cY])

    
    def grabar_video(self):
        while True:
            ret, self.original = self.video.read()

            hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)

            if keyboard.is_pressed('q'): # Romper el loop cuando se aprieta 'q'
                break

            if self.color is None:
                cv2.waitKey(1)
                cv2.imshow('original', self.original)
                continue

            mask = cv2.inRange(hsv_img, self.lower_color, self.upper_color)

            cv2.imshow('original', self.original)

            self.imagen_filtrada = cv2.bitwise_and(self.original, self.original, mask=mask)

            self._anotaciones(mask)

            cv2.waitKey(1)

            cv2.imshow('original', self.original)
            cv2.imshow('filtrada', self.imagen_filtrada)
        
        self.video.release()
        cv2.destroyAllWindows()


    def generar_angulo(self, angulo_limite=45):
        if self.original is not None and self.coordenadas is not None:
            x = self.coordenadas[0] - self.limites[0]
            x = (x / (self.limites[1] - self.limites[0])) - 0.5 # Posición relativa al centro (-0.5 hasta 0.5)
            pos_horizontal = x * ANCHO_CANCHA
            angulo = np.arctan(pos_horizontal/self.distancia)
            angulo = np.rad2deg(angulo)
            angulo = min(angulo_limite, max(-angulo_limite, angulo))
            return angulo