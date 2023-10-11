import cv2
import numpy as np


class Camara:
    def __init__(self, numero_camara, rango=np.array([5, 20, 30])):
        self.rango = rango
        self.color = None
        self.coordenadas = None
        self.ultimas_coordenadas = None
        self.original = None

        self.video = cv2.VideoCapture(numero_camara, cv2.CAP_DSHOW)


    def mouseRGB(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            colorsB = self.original[y, x, 0]
            colorsG = self.original[y, x, 1]
            colorsR = self.original[y, x, 2]
            colors = self.original[y, x]
            hsv_value = np.uint8([[[colorsB, colorsG, colorsR]]])
            hsv = cv2.cvtColor(hsv_value, cv2.COLOR_BGR2HSV)

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

        self.coordenadas = np.array([cX, cY])

    
    def grabar_video(self):
        while True:
            ret, self.original = self.video.read()

            hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)

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

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.video.release()
        cv2.destroyAllWindows()