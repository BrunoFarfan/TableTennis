import time
import serial


class Comunicador:
    def __init__(self, puerto="COM7", baudrate=115200, timeout=3):
        self.comunicador = serial.Serial(port=puerto, baudrate=baudrate, timeout=timeout)
        self.angulo_anterior = 0
    

    def enviar_angulo(self, angulo, espera=0.8):
        time.sleep(espera)
        msgOn = f"{round(angulo)}"
        if abs(angulo - self.angulo_anterior) > 1:
            msgEncode = str.encode(msgOn)
            self.comunicador.write(msgEncode)

            self.angulo_anterior = angulo