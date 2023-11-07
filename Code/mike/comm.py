import time
import serial


class Comunicador:
    def __init__(self, puerto_arduino="COM7", puerto_faulhaber0="COM3",
                 puerto_faulhaber1="COM4", puerto_faulhaber2="COM5", baudrate=115200, timeout=3):
        
        self.arduino = serial.Serial(port=puerto_arduino, baudrate=baudrate, timeout=timeout)
        # self.faulhabers = [
        #     serial.Serial(port=puerto_faulhaber0, baudrate=115200, timeout=timeout),
        #     serial.Serial(port=puerto_faulhaber1, baudrate=115200, timeout=timeout),
        #     serial.Serial(port=puerto_faulhaber2, baudrate=115200, timeout=timeout)
        # ]

        # self.start_faulhabers()

        self.angulo_anterior = 0
    

    def enviar_angulo(self, angulo, espera=0.3):
        if angulo != None:
            time.sleep(espera)
            msgOn = f"{round(angulo)}\n"
            if abs(angulo - self.angulo_anterior) > 1:
                msgEncode = str.encode(msgOn)
                self.arduino.write(msgEncode)

                self.angulo_anterior = angulo


    def start_faulhabers(self):
        msgOn = str.encode("en\n")
        for faulhaber in self.faulhabers:
            msgEncode = str.encode(msgOn)
            faulhaber.write(msgEncode)

    
    def stop_faulhabers(self):
        msgVel = str.encode("v0\n")
        msgOff = str.encode("di\n")
        for faulhaber in self.faulhabers:
            msgEncode = str.encode(msgVel)
            faulhaber.write(msgEncode)
            msgEncode = str.encode(msgOff)
            faulhaber.write(msgEncode)

    
    def enviar_velocidad(self, velocidades, espera=0.3):
        pass