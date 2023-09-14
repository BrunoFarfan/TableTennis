import matplotlib.pyplot as plt
import numpy as np

class PingPong():

    def __init__(self, x0= np.array([0,0,0]), Rw= np.array([0,0,0])):
        # Ball constants
        self.m     = 0.0027    # Masa de pelota en kg
        self.r     = 0.0200    # Radio de pelota en m
        self.R     = 0.0650    # Radio de rodillos en m

        # Coefficients        
        self.CD  = 0.45        # Air friction coefficient
        self.rho = 1.2928      # Aire density in kg/m3
        self.g   = 9.87        # Earth's gravity

        self.pitch = np.deg2rad(29)
        self.yaw = np.deg2rad(0)

        # State variables
        self.x0     = x0                 # Start position of ball      [m]
        self.Rw     = Rw*2*np.pi/60      # Roller's speed              [Rad/s]
        self.w      = np.array([0,0,0])  # Angular velocity of ball    [Rad/s]
        self.x      = np.array([0,0,0])  # Current position of ball    [m]
        self.x_dot  = np.array([0,0,0])  # Linear velocity of ball     [m/s]
        self.x_ddot = np.array([0,0,0])  # Linear acceleration of ball [m/s2]

        # Force enablers
        self.gravity_en = True
        self.drag_en    = True
        self.magnus_en  = True
        self.deltaT = 0.001

        self.reset()
    
    def reset(self):
        # Back to origin
        self.x = self.x0
        # starting linear speed [m/s]
        self.x_dot = self.rotate(np.array([self.R/3 * (self.Rw[0] + self.Rw[1] + self.Rw[2]),0,0]))
        # starting angular speed [Rad/s]
        self.w = self.rotate(np.array([0, np.dot(self.Rw, np.array([-1,0.5,0.5])), np.dot(self.Rw, np.array([0,-np.sqrt(3)/2,np.sqrt(3)/2]))]))

    def rotate(self, x):
        R = np.array([[ np.cos(self.pitch)*np.cos(self.yaw), np.cos(self.pitch)*np.sin(self.yaw), np.sin(self.pitch)],
                      [                   -np.sin(self.yaw),                     np.cos(self.yaw),                   0],
                      [-np.sin(self.pitch)*np.cos(self.yaw), -np.sin(self.pitch)*np.sin(self.yaw), np.cos(self.pitch)]])
        Rinv = np.linalg.inv(R)
        return np.dot(Rinv, x)

    def Fgravity(self):
        if self.gravity_en:
            return np.array([0,0,-self.m*self.g])
        else:
            return np.array([0,0,0])
    
    def Fdrag(self):
        lin_vel = np.linalg.norm(self.x_dot)
        A = np.pi * self.r**2
        if self.drag_en:
            return - 1/2 * self.rho * A * self.CD * lin_vel * self.x_dot
        else:
            return np.array([0,0,0])

    def Fmagnus(self):
        lin_vel = np.linalg.norm(self.x_dot)
        ang_vel = np.linalg.norm(self.w)
        CL = 0.3187*(1 - np.exp(-0.002483 * ang_vel))
        A = np.pi * self.r**2
        if self.magnus_en:
            return 1/2 * CL * self.rho * A * lin_vel * (np.cross(self.w, self.x_dot) / ang_vel)
        else:
            return np.array([0,0,0])

    def step(self, t):
        # Actualizar variables de estado
        self.x_ddot = 1/self.m * (self.Fgravity() + self.Fdrag() + self.Fmagnus())
        self.x_dot = self.x_dot + self.x_ddot*t
        self.x = self.x + self.x_dot*t
    
    def simulate(self):
        xaxis = []
        yaxis = []
        zaxis = []
        xaxis.append(self.x[0])
        yaxis.append(self.x[1])
        zaxis.append(self.x[2])
        hit = False
        while not hit:
            self.step(self.deltaT)
            xaxis.append(self.x[0])
            yaxis.append(self.x[1])
            zaxis.append(self.x[2])
            
            if self.x[2] <= 0:
                # Break when the ball hits the table
                hit = True
        
        return np.round(xaxis, 10), np.round(yaxis, 10), np.round(zaxis, 10)        

    def std_shots(self):
        # Initiate plot
        ax = plt.axes(projection= '3d')
        ax.grid()

        # Ideal
        self.drag_en   = False
        self.magnus_en = False
        self.reset()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)
        print(xaxis[-1])
        
        # Friction
        self.drag_en = True
        self.reset()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)
        print(xaxis[-1])

        # Spin
        self.magnus_en = True
        self.reset()
        xaxis, yaxis, zaxis = self.simulate()
        ax.plot3D(xaxis, yaxis, zaxis)
        print(xaxis[-1])
        
        ax.legend(["Ideal", "Friction", "Spin"])#, "Reverse-spin"]) #, "Left-Spin", "Right-spin"])
        ax.set_title("Standard throws")
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.show()

if __name__ == '__main__':
    
    start_pos     = np.array([0,0,0.47])     # [m]
    rollers_speed = np.array([330,330,330])    # [RPM]
    ball = PingPong(x0= start_pos, Rw= rollers_speed)

    ball.std_shots()
    # max_distance = (0,0)
    # for b in range(-15,16):
    #     ball.yaw = np.deg2rad(b)
    #     for a in range(90):
    #         ball.pitch = np.deg2rad(a)
    #         ball.reset()
    #         x, y, z = ball.simulate()
    #         output = (np.linalg.norm(np.array([x[-1], y[-1], z[-1]])) , a)
    #         max_distance = max(output, max_distance, key= lambda x : x[0])
    # print(max_distance)




