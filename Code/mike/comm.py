import time
import serial
import numpy as np
import threading as th
import re


class Comunicador:
    def __init__(self, puerto_arduino="COM17", puerto_faulhaber0="COM21",
                 puerto_faulhaber1="COM22", puerto_faulhaber2="COM23",
                 baudrate_arduino=115200, baudrate_faulhabers=9600, timeout=3):

        self.lock_faulhabers = th.Lock()
        self.lock_arduino = th.Lock()
        
        self.arduino = serial.Serial(port=puerto_arduino, baudrate=baudrate_arduino, timeout=timeout)
        self.faulhabers = [
            # serial.Serial(port=puerto_faulhaber0, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber1, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber2, baudrate=baudrate_faulhabers, timeout=timeout)
        ]

        self.start_faulhabers()

        self.angulo_anterior = 0
        self.velocidades_anteriores = np.array([0, 0, 0]) # Faulhaber 0, 1 y 2
    

    def enviar_angulo(self, angulo, espera=0):
        if angulo != None:
            with self.lock_arduino:
                time.sleep(espera)
                msgOn = f"{round(angulo)}\n"
                if abs(angulo - self.angulo_anterior) > 1:
                    msgEncode = str.encode(msgOn)
                    self.arduino.write(msgEncode)

                    self.angulo_anterior = angulo


    def enviar_disparo(self):
        with self.lock_faulhabers:
            msgOn = f"True\n"
            msgEncode = str.encode(msgOn)
            self.arduino.write(msgEncode)


    def disparar(self, velocidad, espera_caida_pelota=0.75, detener=True):
        self.enviar_velocidad(velocidades=velocidad)
        self.enviar_disparo()
        time.sleep(espera_caida_pelota) # Esperar para que le de tiempo a la pelota a caer
        if detener:
            self.enviar_velocidad(velocidades=[0, 0, 0])


    def start_faulhabers(self):
        with self.lock_faulhabers:
            msgOn = "en\n"
            for faulhaber in self.faulhabers:
                msgEncode = str.encode(msgOn)
                faulhaber.write(msgEncode)

    
    def stop_faulhabers(self):
        with self.lock_faulhabers:
            msgVel = "v0\n"
            msgOff = "di\n"
            for faulhaber in self.faulhabers:
                msgEncode = str.encode(msgVel)
                faulhaber.write(msgEncode)
                msgEncode = str.encode(msgOff)
                faulhaber.write(msgEncode)

    
    def enviar_velocidad(self, velocidades, n_iteraciones=20, t_aceleracion=1.5):
        if velocidades != None:
            with self.lock_faulhabers:
                velocidades = np.array(velocidades)
                delta = (velocidades - self.velocidades_anteriores) // n_iteraciones
                for _ in range(n_iteraciones):
                    time.sleep(round(t_aceleracion/n_iteraciones, 2))
                    self.velocidades_anteriores += delta

                    msgVel0 = f"v{round(self.velocidades_anteriores[0])}\n"
                    msgEncode = str.encode(msgVel0)
                    self.faulhabers[0].write(msgEncode)

                    # msgVel1 = f"v{round(self.velocidades_anteriores[1])}\n"
                    # msgEncode = str.encode(msgVel1)
                    # self.faulhabers[1].write(msgEncode)

                    msgVel2 = f"v{-round(self.velocidades_anteriores[-1])}\n" # EL TERCER MOTOR TIENE UN MENOS PORQUE TIENE QUE GIRAR EN EL SENTIDO OPUESTO
                    msgEncode = str.encode(msgVel2)
                    self.faulhabers[-1].write(msgEncode)

                print(f"Enviado {self.velocidades_anteriores}")