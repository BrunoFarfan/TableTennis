import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint
import json

class PingPong():

    def __init__(self):
        # Load parameters
        with open(f'parameters.json') as file:
            self.param = json.load(file)
        self.state_0 = np.array(self.param['STATE_0'])
        self.origin = np.array(self.param["ORIGIN"]) # Start position of ball      [m]
        
        # Ball constants
        self.ball_mass  = self.param['BALL_MASS']         # Masa de pelota en kg
        self.ball_radio = self.param['BALL_RADIO']   # Radio de pelota en m
        
        # Roller constants
        self.roller_radio = self.param['ROLLER_RADIO'] # Radio de rodillos en m
        
        # Force coefficients        
        self.CD  = self.param['DRAG_CONSTANT'] # Air friction coefficient
        self.rho = self.param['AIR_DENSITY']   # Aire density in kg/m3
        self.g   = self.param['EARTH_GRAVITY'] # Earth's gravity

        # Force enablers
        self.gravity_en = True
        self.drag_en    = True
        self.magnus_en  = True

        # Initial State
        self.roller_speed = self.state_0 # Roller's speed [Rad/s]
        self.pitch = 0
        self.yaw = 0

        # State variables
        self.ball_pos          = self.state_0        # Current position of ball    [m]
        self.ball_l_speed      = self.state_0        # Linear velocity of ball     [m/s]
        self.ball_a_speed      = self.state_0        # Angular velocity of ball    [Rad/s]
        self.ball_acceleration = self.state_0        # Linear acceleration of ball [m/s2]

        self.reset()
    
    def reset(self, point= None):
        if point != None:
            self.ball_pos = point[:3]
            self.ball_l_speed = point[3:]
        else:
            # Back to origin
            self.ball_pos = self.origin
            # starting linear speed [m/s]
            self.ball_l_speed = self.rotate(np.array([self.roller_radio * np.dot(self.roller_speed, np.array([1/3,1/3,1/3])), 0, 0]))
            # starting angular speed [Rad/s]
            self.ball_a_speed = self.rotate(np.array([0, np.dot(self.roller_speed, np.array([-1,0.5,0.5])), np.dot(self.roller_speed, np.array([0,-np.sqrt(3)/2,np.sqrt(3)/2]))]))

    def rotate(self, x):
        R = np.array([[ np.cos(self.pitch)*np.cos(self.yaw), np.cos(self.pitch)*np.sin(self.yaw), np.sin(self.pitch)],
                      [                   -np.sin(self.yaw),                     np.cos(self.yaw),                   0],
                      [-np.sin(self.pitch)*np.cos(self.yaw), -np.sin(self.pitch)*np.sin(self.yaw), np.cos(self.pitch)]])
        Rinv = np.linalg.inv(R)
        return np.dot(Rinv, x)

    def Fgravity(self):
        if self.gravity_en:
            return np.array([0,0,-self.ball_mass*self.g])
        else:
            return np.array([0,0,0])
    
    def Fdrag(self):
        lin_vel = np.linalg.norm(self.ball_l_speed)
        A = np.pi * self.ball_radio**2
        if self.drag_en:
            return - 1/2 * self.rho * A * self.CD * lin_vel * self.ball_l_speed
        else:
            return np.array([0,0,0])

    def Fmagnus(self):
        lin_vel = np.linalg.norm(self.ball_l_speed)
        ang_vel = np.linalg.norm(self.ball_a_speed)
        CL = 0.3187*(1 - np.exp(-0.002483 * ang_vel))
        A = np.pi * self.ball_radio**2
        if self.magnus_en:
            return 1/2 * CL * self.rho * A * lin_vel * (np.cross(self.ball_a_speed, self.ball_l_speed) / ang_vel)
        else:
            return np.array([0,0,0])

    def model(self, current_state, t):
        dxdt, dydt, dzdt = current_state
        self.reset(point= current_state) # Set new state to class variables

        d2xdt2 = 1/self.ball_mass * (self.Fgravity() + self.Fdrag() + self.Fmagnus())[0]
        d2ydt2 = 1/self.ball_mass * (self.Fgravity() + self.Fdrag() + self.Fmagnus())[1]
        d2zdt2 = 1/self.ball_mass * (self.Fgravity() + self.Fdrag() + self.Fmagnus())[2]

        return [dxdt, dydt, dzdt, d2xdt2, d2ydt2, d2zdt2]

    def step(self, max_time):
        time_points = np.linspace(0, max_time, int(100*max_time))
        self.reset()

        ball_trajectory = odeint(self.model, self.ball_pos, time_points)
        
        xyz_points = {"x": ball_trajectory[:, 0],
                      "y": ball_trajectory[:, 1],
                      "z": ball_trajectory[:, 2]}
        
        return xyz_points


    def simulate(self, sim_state, time, end= False):
        self.roller_speed = sim_state['roller_speed']*2*np.pi/60  # [Rad/s]
        self.pitch = sim_state['pitch']
        self.yaw = sim_state['yaw']
        self.reset()
        # Simulate the trajectory for the given rollers speeds
        xaxis, yaxis, zaxis = self.step(time)

        ax = plt.axes(projection= '3d')
        ax.grid()

        ax.plot3D(xaxis, yaxis, zaxis)
        
        ax.legend([f"{self.roller_speed} RPM"])
        ax.set_title("Standard throws")
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')

        if not end:
            plt.draw()
        else:
            plt.show()