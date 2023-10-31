import cv2
import numpy as np
import time


class Camara:
    def __init__(self, numero_camara, rango=np.array([0, 0, 30])):
        self.rango = rango
        self.color = None
        self.lower_color = None
        self.upper_color = None
        self.coordenadas = None
        self.ultimas_coordenadas = None

        self.time = 0
        self.count = 0
        self.max_count = 5
        self.thresh = 15
        self.kernel = np.ones((5,5), np.uint8)

        self.original = None
        self.img_out = None
        self.move_mask = None
        self.temp_background = None
        self.background = [None]*self.max_count

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

        self.time = time.time()
        self.grabar_video()


    def _anotaciones(self, mask):
        M = cv2.moments(mask)

        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            self.ultimas_coordenadas = np.array([cX, cY])
        else:
            cX, cY = self.ultimas_coordenadas

        cv2.circle(self.img_out, (cX, cY), 5, (255, 255, 255), -1)
        cv2.putText(self.img_out, "centroid", (cX - 25, cY - 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        self.coordenadas = np.array([cX, cY])

    def update_background(self, step):
        if step == 1:
            return cv2.absdiff(self.background[step], self.background[0])
        return cv2.absdiff(cv2.absdiff(self.background[step], self.background[0]), self.update_background(step= step-1))
    
    # def update_background(self, step):
    #     for frame in self.background[:-2]:
    #         diff = cv2.absdiff(diff, cv2.absdiff(frame, self.background[-1]))
    #     if step == 0:
    #         return self.background[0]
    #     return cv2.absdiff(self.background[step], self.update_background(step= step-1))

    def grabar_video(self):
        while True:
            ret, self.original = self.video.read()
            hsv_img = cv2.cvtColor(self.original, cv2.COLOR_BGR2HSV)
            
            if self.count < self.max_count:
                self.img_out = np.ones(hsv_img.shape[:2])
                self.move_mask = self.original
                self.temp_background = self.original
                self.background.pop(0)
                self.background.append(hsv_img)
                self.count += 1
            else:
                self.background.pop(0)
                self.background.append(hsv_img)
                self.temp_background = self.update_background(step = self.max_count-1)
                self.move_mask = cv2.cvtColor(cv2.cvtColor(self.temp_background, cv2.COLOR_HSV2BGR), cv2.COLOR_BGR2GRAY)
                ret, self.move_mask = cv2.threshold(self.move_mask, self.thresh, 255, cv2.THRESH_BINARY)
                self.move_mask = cv2.morphologyEx(self.move_mask, cv2.MORPH_OPEN, self.kernel)
                self.move_mask = cv2.dilate(self.move_mask, self.kernel, iterations= 10)
                # flood_mask = np.zeros((self.move_mask.shape[0]+2, self.move_mask.shape[1]+2), np.uint8)
                # cv2.floodFill(self.move_mask, flood_mask, (0,0), 255)
                # self.move_mask = cv2.erode(self.move_mask, self.kernel, iterations= 25)
                self.img_out = self.move_mask
                # self.img_out = cv2.morphologyEx(self.move_mask, cv2.MORPH_OPEN, self.kernel)
                # self.img_out = np.zeros((self.original.shape[0], self.original.shape[1], 3))
                # self.img_out[:,:,0] = self.move_mask
                # self.img_out[:,:,1] = self.move_mask
                # self.img_out[:,:,2] = self.move_mask

                # # temp_h = self.temp_background[:,:,0]
                # temp_s = self.temp_background[:,:,1]
                # temp_v = self.temp_background[:,:,2]
                # # ret, thresh_h = cv2.threshold(temp_h, self.rango[0], 255, cv2.THRESH_BINARY)
                # ret, thresh_s = cv2.threshold(temp_s, self.rango[1], 255, cv2.THRESH_BINARY)
                # ret, thresh_v = cv2.threshold(temp_v, self.rango[2], 255, cv2.THRESH_BINARY)
                # self.temp_background[:,:,0] = np.ones((self.temp_background.shape[:2]))
                # self.temp_background[:,:,1] = np.ones((self.temp_background.shape[:2]))*255
                # self.temp_background[:,:,2] = thresh_v
                # # self.move_mask = self.temp_background # cv2.cvtColor(self.temp_background, cv2.COLOR_HSV2BGR)

            # if self.color is None:
            #     cv2.waitKey(1)
            #     cv2.imshow('original', self.original)
            #     continue
            
            if not (self.color is None):
                mask = cv2.inRange(hsv_img, self.lower_color, self.upper_color)
                self.img_out = cv2.bitwise_and(self.img_out, self.img_out, mask= mask)
                
            # # cv2.imshow('original', self.img_out)

            # self.imagen_filtrada = cv2.bitwise_and(self.img_out, self.img_out, mask=mask)

            self._anotaciones(self.img_out)

            cv2.waitKey(1)

            cv2.imshow('original', self.original)
            cv2.imshow('filtrada', self.img_out)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.video.release()
        cv2.destroyAllWindows()