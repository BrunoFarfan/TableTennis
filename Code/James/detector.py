import cv2
import numpy as np


class DetectorMaestro():
    
    def __init__(self, modo= 0,
                    rango_color= np.array([5, 50, 50]),
                    max_layers= 5, thresh= 15, kernel= np.ones((5,5), np.uint8),
                    rango_cara= (30, 70), d_angle= 60, angle_tolerance= 5):
        self.modo = modo
        
        # Entrada
        self.original = None

        # Salida
        self.filtrada = None
        self.limites = []
        self.coordenadas = None

        # Detector de color
        self.rango_color = rango_color
        self.color = None
        self.lower_color = None
        self.upper_color = None

        # Detector de movimiento
        self.layers_count = 0
        self.max_layers = max_layers
        self.thresh = thresh
        self.kernel = kernel
        self.temp_background = None
        self.background = [None]*self.max_layers

        # Detector de cara y posicionamiento automático
        self.edged = None
        self.lines = []
        self.minSize = (rango_cara[0], rango_cara[0])
        self.maxSize = (rango_cara[1], rango_cara[1])
        self.diagonal_angle = d_angle
        self.angle_tolerance = angle_tolerance


    def mouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_RBUTTONDOWN:
            colorsB = self.original[y, x, 0]
            colorsG = self.original[y, x, 1]
            colorsR = self.original[y, x, 2]
            colors = self.original[y, x]
            hsv_value = np.uint8([[[colorsB, colorsG, colorsR]]])
            hsv = cv2.cvtColor(hsv_value, cv2.COLOR_BGR2HSV)

            self.lower_color = hsv - self.rango_color
            self.upper_color = hsv + self.rango_color

            self.color = hsv
        
        elif event == cv2.EVENT_LBUTTONDOWN and len(self.limites) < 2:
            self.limites.append(x)
    
    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.coordenadas = np.array([cX, cY])

        cv2.circle(self.filtrada, self.coordenadas, 5, (255, 255, 255), -1)
        cv2.putText(self.filtrada, "centroid", (self.coordenadas[0] - 25,
                                                       self.coordenadas[1] - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if len(self.limites) == 2:
            izquierdo = self.limites[0]
            derecho = self.limites[1]

            cv2.line(self.filtrada, np.array([izquierdo, 0]),
                     np.array([izquierdo, len(self.original)]), (255, 255, 255), 3)
            cv2.line(self.filtrada, np.array([derecho, 0]),
                     np.array([derecho, len(self.original)]), (255, 255, 255), 3)
    
    #########################
    ### Detector de Color ###
    #########################
    
    def filtroColor(self):
        if self.color is None:
            return (self.original, self.limites, self.coordenadas)
        
        if self.modo == 3:
            self.original = cv2.bitwise_and(self.original, self.original, mask= self.filtrada)

        hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv_img, self.lower_color, self.upper_color)
       
        self.filtrada = cv2.bitwise_and(self.original, self.original, mask= mask)

        self._anotaciones(mask)

        return (self.filtrada, self.limites, self.coordenadas)
    
    ##############################
    ### Detector de Movimiento ###
    ##############################

    def update_background(self, step):
        if step == 1:
            return cv2.absdiff(self.background[step], self.background[0])
        return cv2.absdiff(cv2.absdiff(self.background[step], self.background[0]),
                           self.update_background(step= step-1))
    
    def filtroMovimiento(self):
        hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)
            
        if self.layers_count < self.max_layers:
            self.filtrada = self.original
            self.temp_background = self.original
            self.background.pop(0)
            self.background.append(hsv_img)
            self.layers_count += 1
        else:
            self.background.pop(0)
            self.background.append(hsv_img)
            self.temp_background = self.update_background(step = self.max_layers-1)
            self.filtrada = cv2.cvtColor(cv2.cvtColor(self.temp_background, cv2.COLOR_HSV2BGR),
                                          cv2.COLOR_BGR2GRAY)
            ret, self.filtrada = cv2.threshold(self.filtrada, self.thresh, 255, cv2.THRESH_BINARY)
            self.filtrada = cv2.morphologyEx(self.filtrada, cv2.MORPH_OPEN, self.kernel)
            self.filtrada = cv2.dilate(self.filtrada, self.kernel, iterations= 5)

            self._anotaciones(self.filtrada)

        return (self.filtrada, self.limites, self.coordenadas)
    
    #########################
    ### Detector de Caras ###
    #########################
    
    def haar(self):
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(self.original, minNeighbors=5, minSize= self.minSize, maxSize= self.maxSize)
        if len(faces) > 0:
            max = 0
            j = 0
            for i in range(len(faces)):
                if faces[i][2] > max:
                    max = faces[i][2]
                    j = i
            
            x, y, w, h = faces[j]
            cv2.rectangle(self.filtrada, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(self.filtrada, "Jugador 1", (x - 5, y - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            self.coordenadas = np.array([x, y])

    def table(self):
        gray_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
        self.edged = cv2.Canny(gray_img, 200, 1000, None, 7)
        self.lines = cv2.HoughLines(self.edged, 2, np.pi / 360, 200, None, 0, 0)
        
                       
        if self.lines is not None:
                pt1_h = pt1_d1 = pt1_d2 = 0
                n_h = 1000
                n_d1 = n_d2 = -1000
                for i in range(0, len(self.lines)):
                    rho = self.lines[i][0][0]
                    theta = self.lines[i][0][1]
                    if abs(theta) >= np.deg2rad(90-self.angle_tolerance) and abs(theta) <= np.deg2rad(90+self.angle_tolerance):
                        # Linea Hoirizontal
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        m_h0 = np.tan(-theta + np.sign(theta)*np.pi/2)
                        n_h0 = y0 + x0*m_h0
                        pt1_h0 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
                        pt2_h0 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
                        if n_h0 < n_h and y0 > 300:
                            pt1_h = pt1_h0
                            pt2_h = pt2_h0
                            m_h   = m_h0
                            n_h   = n_h0
                    elif theta >= np.deg2rad(self.diagonal_angle - self.angle_tolerance) and theta <= np.deg2rad(self.diagonal_angle + self.angle_tolerance):
                        # Diagonal izquierda
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        m_d10 = np.tan(-theta + np.sign(theta)*np.pi/2)
                        n_d10 = y0 + x0*m_d10
                        pt1_d10 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
                        pt2_d10 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
                        if (n_d10 < n_d1 or n_d1 == -1000)  and y0 > 300:
                            pt1_d1 = pt1_d10
                            pt2_d1 = pt2_d10
                            m_d1   = m_d10
                            n_d1   = n_d10
                    elif theta >= np.pi-np.deg2rad(self.diagonal_angle + self.angle_tolerance) and theta <= np.pi-np.deg2rad(self.diagonal_angle - self.angle_tolerance):
                        # Diagonal derecha
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        m_d20 = np.tan(-theta + np.sign(theta)*np.pi/2)
                        n_d20 = y0 + x0*m_d20
                        pt1_d20 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
                        pt2_d20 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
                        if n_d20 > n_d2 and y0 > 300:
                            pt1_d2 = pt1_d20
                            pt2_d2 = pt2_d20
                            m_d2   = m_d20
                            n_d2   = n_d20
                
                # Declarar intersecciones cuando se encuentren las tres rectas
                p = 0
                if pt1_h != 0:
                    cv2.line(self.filtrada, pt1_h, pt2_h, (0,0,255), 2, cv2.LINE_AA)
                    p += 1
                if pt1_d1 != 0:
                    cv2.line(self.filtrada, pt1_d1, pt2_d1, (0,0,255), 2, cv2.LINE_AA)
                    p += 1
                if pt1_d2 != 0:
                    cv2.line(self.filtrada, pt1_d2, pt2_d2, (0,0,255), 2, cv2.LINE_AA)
                    p += 1
                if p == 3:
                    l1 = np.array([(n_h-n_d1)/(m_h - m_d1) , (n_d1*m_h - n_h*m_d1)/(m_h - m_d1)], dtype= np.int32)
                    l2 = np.array([(n_h-n_d2)/(m_h - m_d2) , (n_d2*m_h - n_h*m_d2)/(m_h - m_d2)], dtype= np.int32)
                    cv2.circle(self.filtrada, l1, 3, (255, 0, 0), -1)
                    cv2.circle(self.filtrada, l2, 3, (255, 0, 0), -1)
                    self.limites = [l1, l2]

    def filtroCara(self):
        self.filtrada = self.original
        self.haar()    # Encontrar jugador
        self.table()   # Delimitar mesa de juego
        return (self.filtrada, self.limites, self.coordenadas)
        
    
    #################################################################################################################################################
    
    def filtrar(self):
        if self.modo == 0:
            return self.filtroCara()
        elif self.modo == 1:
            return self.filtroColor()
        elif self.modo == 2:
            return self.filtroMovimiento()
        elif self.modo == 3:
            self.filtroMovimiento()
            return self.filtroColor()
        
        # Default case
        return self.filtroColor()