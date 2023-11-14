import cv2
import numpy as np


class DetectorColor:
    def __init__(self, rango):
        self.original = None
        self.rango = rango
        self.color = None
        self.limites = [] # [izquierdo, derecho]


    def mouseClick(self, event, x, y, flags, param):
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

    
    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.ultimas_coordenadas = np.array([cX, cY])
        else:
            cX, cY = self.ultimas_coordenadas

        cv2.circle(self.imagen_filtrada, (cX, cY), 5, (255, 255, 255), -1)
        cv2.putText(self.imagen_filtrada, "centroid", (cX - 25, cY - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if len(self.limites) == 2:
            izquierdo = self.limites[0]
            derecho = self.limites[1]

            cv2.line(self.imagen_filtrada, np.array([izquierdo, 0]),
                     np.array([izquierdo, len(self.original)]), (255, 255, 255), 3)
            cv2.line(self.imagen_filtrada, np.array([derecho, 0]),
                     np.array([derecho, len(self.original)]), (255, 255, 255), 3)

        self.coordenadas = np.array([cX, cY])

    
    def filtrar(self):
        hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv_img, self.lower_color, self.upper_color)

        self.imagen_filtrada = cv2.bitwise_and(self.original, self.original, mask=mask)

        self._anotaciones(mask)

        return (self.imagen_filtrada, self.limites)
    


class DetectorMovimiento:
    def __init__(self, max_layers=5, thresh=15, kernel=np.ones((5,5), np.uint8)):
        self.layers_count = 0
        self.max_layers = max_layers
        self.thresh = thresh
        self.kernel = kernel

        self.original = None
        self.imagen_filtrada = None
        self.move_mask = None
        self.temp_background = None
        self.background = [None]*self.max_layers

        self.limites = [] # [izquierdo, derecho]


    def mouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(self.limites) < 2:
            self.limites.append(x)


    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.ultimas_coordenadas = np.array([cX, cY])
        else:
            cX, cY = self.ultimas_coordenadas

        cv2.circle(self.imagen_filtrada, (cX, cY), 5, (255, 255, 255), -1)
        cv2.putText(self.imagen_filtrada, "centroid", (cX - 25, cY - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if len(self.limites) == 2:
            izquierdo = self.limites[0]
            derecho = self.limites[1]

            cv2.line(self.imagen_filtrada, np.array([izquierdo, 0]),
                     np.array([izquierdo, len(self.original)]), (255, 255, 255), 3)
            cv2.line(self.imagen_filtrada, np.array([derecho, 0]),
                     np.array([derecho, len(self.original)]), (255, 255, 255), 3)

        self.coordenadas = np.array([cX, cY])


    def update_background(self, step):
        if step == 1:
            return cv2.absdiff(self.background[step], self.background[0])
        return cv2.absdiff(cv2.absdiff(self.background[step], self.background[0]),
                           self.update_background(step= step-1))
    

    def filtrar(self):
        hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)
            
        if self.layers_count < self.max_layers:
            self.imagen_filtrada = np.ones(hsv_img.shape[:2])
            self.move_mask = self.original
            self.temp_background = self.original
            self.background.pop(0)
            self.background.append(hsv_img)
            self.layers_count += 1
        else:
            self.background.pop(0)
            self.background.append(hsv_img)
            self.temp_background = self.update_background(step = self.max_layers-1)
            self.move_mask = cv2.cvtColor(cv2.cvtColor(self.temp_background, cv2.COLOR_HSV2BGR),
                                          cv2.COLOR_BGR2GRAY)
            ret, self.move_mask = cv2.threshold(self.move_mask, self.thresh, 255, cv2.THRESH_BINARY)
            self.move_mask = cv2.morphologyEx(self.move_mask, cv2.MORPH_OPEN, self.kernel)
            self.move_mask = cv2.dilate(self.move_mask, self.kernel, iterations= 5)

            self.imagen_filtrada = self.move_mask

        self._anotaciones(self.imagen_filtrada)

        return (self.imagen_filtrada, self.limites)