import time
import serial
import numpy as np
import threading as th
import re


class Comunicador:
    def __init__(self, puerto_arduino="COM17", puerto_faulhaber0="COM21",
                 puerto_faulhaber1="COM22", puerto_faulhaber2="COM23",
                 baudrate_arduino=115200, baudrate_faulhabers=9600, timeout=3):

        self.serial_lock = th.Lock()
        
        self.arduino = serial.Serial(port=puerto_arduino, baudrate=baudrate_arduino, timeout=timeout)
        self.faulhabers = [
            serial.Serial(port=puerto_faulhaber0, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber1, baudrate=baudrate_faulhabers, timeout=timeout),
            serial.Serial(port=puerto_faulhaber2, baudrate=baudrate_faulhabers, timeout=timeout)
        ]

        self.start_faulhabers()

        self.angulo_anterior = 0
        self.velocidades_anteriores = np.array([0, 0, 0]) # Faulhaber 0, 1 y 2
    

    def enviar_angulo(self, angulo, espera=0):
        if angulo != None:
            with self.serial_lock:
                time.sleep(espera)
                msgOn = f"{round(angulo)}\n"
                if abs(angulo - self.angulo_anterior) > 1:
                    msgEncode = str.encode(msgOn)
                    self.arduino.write(msgEncode)

                    self.angulo_anterior = angulo


    def leer_error_angulo(self):
        with self.serial_lock:
            linea = self.arduino.readline().decode('utf-8').strip()
            try:
                error_actual = linea.split(",")[-2] # El penúltimo valor es el error
                match = re.search(r'\b(\d+)\b', error_actual) # Buscar el número en el string
                return int(match.group(0))
            except IndexError:
                return None

            
    # Aquí habría que mandarle al servo la señal de dejar pasar 1 pelota pero
    # hay que hacer girar los rodillos antes de mandar la señal de disparo
    def disparar(self):
        self.enviar_velocidad([1000, 1000, 1000]) # Girar los rodillos temporalmente para ver si funciona
        time.sleep(0.5)
        self.enviar_velocidad([0, 0, 0])


    def start_faulhabers(self):
        with self.serial_lock:
            msgOn = "en\n"
            for faulhaber in self.faulhabers:
                msgEncode = str.encode(msgOn)
                faulhaber.write(msgEncode)

    
    def stop_faulhabers(self):
        with self.serial_lock:
            msgVel = "v0\n"
            msgOff = "di\n"
            for faulhaber in self.faulhabers:
                msgEncode = str.encode(msgVel)
                faulhaber.write(msgEncode)
                msgEncode = str.encode(msgOff)
                faulhaber.write(msgEncode)

    
    def enviar_velocidad(self, velocidades, n_iteraciones=20, t_aceleracion=1.5):
        if velocidades != None:
            with self.serial_lock:
                velocidades = np.array(velocidades)
                delta = (velocidades - self.velocidades_anteriores) // n_iteraciones
                for _ in range(n_iteraciones):
                    time.sleep(round(t_aceleracion/n_iteraciones, 2))
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