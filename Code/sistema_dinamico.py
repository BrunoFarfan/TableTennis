from matplotlib.pyplot import plot
import numpy as np
from scipy.integrate import odeint

class PingPong():

    def __init__(self):
        self.wx, self.wy, self. wz = 0    # Velocidad angular

    def modelar(self, state,t):
        px = state[0]    # Velocidad en X
        vx = state[1]    # Posición en X
        py = state[0]    # Velocidad en X
        vy = state[1]    # Posición en X
        px = state[0]    # Velocidad en X
        vx = state[1]    # Posición en X


        # Edo de segundo orden dividida en dos edos de primer orden
        dxdt = v
        dvdt = self.wy*
