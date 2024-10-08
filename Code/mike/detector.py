import cv2
import numpy as np
import abc


class Detector:
    def __init__(self):
        self.original = None
        self.imagen_filtrada = None
        self.limites = [] # [izquierdo, derecho]
        self.coordenadas = None


    @abc.abstractmethod
    def mouseClick(self, event, x, y, flags, param):
        pass


    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.coordenadas = np.array([cX, cY])

        cv2.circle(self.imagen_filtrada, self.coordenadas, 5, (255, 255, 255), -1)
        cv2.putText(self.imagen_filtrada, "centroid", (self.coordenadas[0] - 25,
                                                       self.coordenadas[1] - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if len(self.limites) == 2:
            izquierdo = self.limites[0]
            derecho = self.limites[1]

            cv2.line(self.imagen_filtrada, np.array([izquierdo, 0]),
                     np.array([izquierdo, len(self.original)]), (255, 255, 255), 3)
            cv2.line(self.imagen_filtrada, np.array([derecho, 0]),
                     np.array([derecho, len(self.original)]), (255, 255, 255), 3)
        

    @abc.abstractmethod
    def filtrar(self):
        pass


class DetectorColor(Detector):
    def __init__(self, rango= np.array([5, 50, 100])):
        super().__init__()

        self.rango = rango
        self.color = None


    def mouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_RBUTTONDOWN:
            colorsB = self.original[y, x, 0]
            colorsG = self.original[y, x, 1]
            colorsR = self.original[y, x, 2]
            colors = self.original[y, x]
            hsv_value = np.uint8([[[colorsB, colorsG, colorsR]]])
            hsv = cv2.cvtColor(hsv_value, cv2.COLOR_BGR2HSV)

            self.lower_color = hsv - self.rango
            self.upper_color = hsv + self.rango

            self.color = hsv
        
        elif event == cv2.EVENT_LBUTTONDOWN and len(self.limites) < 2:
            self.limites.append(x)

    
    def filtrar(self):
        hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv_img, self.lower_color, self.upper_color)

        self.imagen_filtrada = cv2.bitwise_and(self.original, self.original, mask=mask)

        self._anotaciones(mask)

        return (self.imagen_filtrada, self.limites, self.coordenadas)
    


class DetectorMovimiento(Detector):
    def __init__(self, distancia= 0.5, max_layers= 5, thresh= 15, kernel= np.ones((5,5), np.uint8)):
        super().__init__()

        self.distancia = distancia
        self.layers_count = 0
        self.max_layers = max_layers
        self.thresh = thresh
        self.kernel = kernel
        self.temp_background = None
        self.background = [None]*self.max_layers
        self.move_mask = None


    def mouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(self.limites) < 2:
            self.limites.append(x)


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

        return (self.imagen_filtrada, self.limites, self.coordenadas)
    

    
# Detector de movimiento y color. Funciona igual que el anterior, pero instancia el detector de color y movimiento
# dentro de la clase, en vez de copiar sus metodos dentro. No tiene sus propios métodos de filtrar, sino que
# llama a los de los detectores de color y movimiento.
class DetectorMovimientoColor(Detector):
    def __init__(self,
                rango= np.array([5, 50, 100]),
                max_layers= 5, thresh= 15, kernel= np.ones((5,5), np.uint8)):
        super().__init__()

        self.detector_color = DetectorColor(rango= rango)
        self.detector_movimiento = DetectorMovimiento(max_layers= max_layers, thresh= thresh, kernel= kernel)

        self.color = None


    def mouseClick(self, event, x, y, flags, param):
        self.detector_color.original = self.original
        self.detector_color.mouseClick(event, x, y, flags, param)

        self.color = self.detector_color.color

    
    def filtrar(self):
        self.detector_movimiento.original = self.original

        if self.color is None:
            return (self.original, self.limites, self.coordenadas)
        
        self.detector_movimiento.filtrar()

        # se hace este cambio de tipo porque la mascara de movimiento es de tipo float64, y la mascara de color es de tipo uint8
        mask = (self.detector_movimiento.imagen_filtrada * 255).astype(np.uint8)

        self.detector_color.original = cv2.bitwise_and(self.original, self.original, mask=mask)
        
        self.imagen_filtrada, self.limites, self.coordenadas = self.detector_color.filtrar()

        return (self.imagen_filtrada, self.limites, self.coordenadas)