import matplotlib.pyplot as plt
import numpy as np

class PingPong():

    def __init__(self, x0= np.array([0,0,0]), w0= np.array([0,0,0])):
        self.m     = 0.027    # Masa de pelota en kg
        self.r     = 0.2000    # Radio de pelota en m
        self.R     = 0.2000    # Radio de rodillos en m
        self.phi   = 180       # Rotación de sistema en 360°
        self.ytrig = np.array([np.cos(np.deg2rad(self.phi)), -np.sin(np.deg2rad(self.phi + 30)), -np.cos(np.deg2rad(self.phi + 60))])
        self.ztrig = np.array([np.sin(np.deg2rad(self.phi)), np.cos(np.deg2rad(self.phi + 30)), -np.sin(np.deg2rad(self.phi + 60))])
        
        self.Cr0 = 0.47
        self.Cr  = 0.47   # Coeficiente de roce de aire
        self.CM0 = 0.1
        self.CM  = 0.1      # Constante de Magnus (0.1-0.5)
        
        self.rho = 1.2928   # Densidad del aire en kg/m3
        self.g   = 9.87     # Constante de gravedad
        
        # Velocidad angular de la pelota
        self.W = np.array([0,0,0])
        self.A = np.array([
            [-self.Cr, -self.KM()*self.W[2], self.KM()*self.W[1]],
            [self.KM()*self.W[2], -self.Cr, -self.KM()*self.W[0]],
            [-self.KM()*self.W[1], self.KM()*self.W[0], -self.Cr]
        ])
        self.B = np.array([0,0,-self.m*self.g])    # Fuerzas conservativas


        # Variables de estado
        self.x0     = x0                 # Starting point
        self.w0     = w0                 # Roller's speed
        self.x      = np.array([0,0,0])  #  x,  y,  z
        self.x_dot  = np.array([0,0,0])  # vx, vy, vz
        self.x_ddot = np.array([0,0,0])  # ax, ay, az

        self.deltaT = 0.001

        self.reset()
    
    def reset(self):
        # Back to origin
        self.x = self.x0

        # linear speed [m/s]
        self.x_dot = v0
        # self.x_dot = np.array([self.r * np.mean(self.w0),0,0])
        # angular speed [Rad/s]
        self.W = W0
        # self.W = np.array([0, np.dot(self.w0, self.ytrig), np.dot(self.w0, self.ztrig)])
        # Reset A
        self.update_A()
    
    def KM(self):
        return 1/2 * self.CM * self.rho * (4 * np.pi * self.r**2) * self.r 

    def update_A(self):
        self.A = np.array([
            [-self.Cr, -self.KM()*self.W[2], self.KM()*self.W[1]],
            [self.KM()*self.W[2], -self.Cr, -self.KM()*self.W[0]],
            [-self.KM()*self.W[1], self.KM()*self.W[0], -self.Cr]
        ])

    def step(self, t):
        # Actualizar variables de estado
        self.x_ddot = np.dot(self.A, self.x_dot) + np.transpose(self.B)
        self.x_dot = self.x_dot + self.x_ddot*t
        self.x = self.x + self.x_dot*t
    
    def simulate(self):
        xaxis = []
        yaxis = []
        zaxis = []
        xaxis.append(x0[0])
        yaxis.append(x0[1])
        zaxis.append(x0[2])
        hit = False
        while not hit:
            self.step(self.deltaT)
            xaxis.append(self.x[0])
            yaxis.append(self.x[1])
            zaxis.append(self.x[2])
            
            if self.x[2] <= 0:
                # Break when the ball hits the table
                hit = True
        
        return xaxis, yaxis, zaxis        

    def std_shots(self):
        # Initiate plot
        ax = plt.axes(projection= '3d')
        ax.grid()

        # Ideal
        self.Cr = 0
        self.CM = 0
        self.reset()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)
        
        # Friction
        self.Cr = self.Cr0
        self.reset()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)

        # Top-Spin
        self.CM = self.CM0
        self.reset()
        print(self.W)
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)        
        
        # Back-Spin
        self.reset()
        self.W = -W0
        self.update_A()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)
        
        ax.legend(["Ideal", "Friction", "Top-Spin", "Back-spin"]) #, "Left-Spin", "Right-spin"])
        ax.set_title("Standard throws")
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.show()

if __name__ == '__main__':
    
    x0 = np.array([0,0,0.3])
    v0 = np.array([8.7,0,0])
    W0 = np.array([0,4,0])
    ball = PingPong(x0= x0)

    ball.std_shots()
    



