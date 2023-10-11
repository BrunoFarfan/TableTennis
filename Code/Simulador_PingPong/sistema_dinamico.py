import numpy as np
from ping_pong import PingPong

if __name__ == '__main__':
    ball = PingPong()
    
    sim_time = 1  # 1 second
    state01 = {"roller_speed" : np.array([330,330,330]),
               "pitch" : 0,
               "yaw"   : 0}
    ball.simulate(sim_state= state01, time= sim_time, end= True)




