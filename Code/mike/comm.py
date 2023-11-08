import time
import serial
import numpy as np


class Comunicador:
    def __init__(self, puerto_arduino="COM17", puerto_faulhaber0="COM21",
                 puerto_faulhaber1="COM22", puerto_faulhaber2="COM23",
                 baudrate_arduino=115200, baudrate_faulhabers=9600, timeout=3):
        
        self.arduino = serial.Serial(port=puerto_arduino, baudrate=baudrate_arduino, timeout=timeout)
        self.faulhabers = [
            serial.Serial(port=puerto_faulhaber0, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber1, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber2, baudrate=baudrate_faulhabers, timeout=timeout)
        ]

        self.start_faulhabers()

        self.angulo_anterior = 0
        self.velocidades_anteriores = np.array([0, 0, 0]) # Faulhaber 0, 1 y 2
    

    def enviar_angulo(self, angulo, espera=0.3):
        if angulo != None:
            time.sleep(espera)
            msgOn = f"{round(angulo)}\n"
            if abs(angulo - self.angulo_anterior) > 1:
                msgEncode = str.encode(msgOn)
                self.arduino.write(msgEncode)

                self.angulo_anterior = angulo


    def start_faulhabers(self):
        msgOn = "en\n"
        for faulhaber in self.faulhabers:
            msgEncode = str.encode(msgOn)
            faulhaber.write(msgEncode)

    
    def stop_faulhabers(self):
        msgVel = "v0\n"
        msgOff = "di\n"
        for faulhaber in self.faulhabers:
            msgEncode = str.encode(msgVel)
            faulhaber.write(msgEncode)
            msgEncode = str.encode(msgOff)
            faulhaber.write(msgEncode)

    
    def enviar_velocidad(self, velocidades, n_iteraciones=10):
        if velocidades != None:
            msgVel0, msgVel1, msgVel2 = "No actualizado", "No actualizado", "No actualizado"
            if len(velocidades) == 1:
                velocidades = [velocidades[0], velocidades[0], velocidades[0]]
            velocidades = np.array(velocidades)
            delta = (velocidades - self.velocidades_anteriores) // n_iteraciones
            for i in range(n_iteraciones):
                time.sleep(round(1/n_iteraciones, 1))
                self.velocidades_anteriores += delta

                msgVel0 = f"v{round(self.velocidades_anteriores[0])}\n"
                msgEncode = str.encode(msgVel0)
                self.faulhabers[0].write(msgEncode)

                msgVel1 = f"v{round(self.velocidades_anteriores[1])}\n"
                msgEncode = str.encode(msgVel1)
                self.faulhabers[1].write(msgEncode)

                msgVel2 = f"v{-round(self.velocidades_anteriores[2])}\n" # EL TERCER MOTOR TIENE UN MENOS PORQUE TIENE QUE GIRAR EN EL SENTIDO OPUESTO
                msgEncode = str.encode(msgVel2)
                self.faulhabers[2].write(msgEncode)

                print(f"Enviado {msgVel0, msgVel1, msgVel2}")