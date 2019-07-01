import numpy as np
from physics_sim import PhysicsSim

class Task():
    """Task (environment) that defines the goal and provides feedback to the agent."""
    def __init__(self, init_pose=None, init_velocities=None, 
        init_angle_velocities=None, runtime=5., target_pos=None):
        """Initialize a Task object.
        Params
        ======
            init_pose: initial position of the quadcopter in (x,y,z) dimensions and the Euler angles
            init_velocities: initial velocity of the quadcopter in (x,y,z) dimensions
            init_angle_velocities: initial radians/second for each of the three Euler angles
            runtime: time limit for each episode
            target_pos: target/goal (x,y,z) position for the agent
        """
        # Simulation
        self.sim = PhysicsSim(init_pose, init_velocities, init_angle_velocities, runtime) 
        self.action_repeat = 3

        self.state_size = self.action_repeat * 6
        self.action_low = 0
        self.action_high = 900
        self.action_size = 4
        

        # Goal
        self.target_pos = target_pos if target_pos is not None else np.array([0., 0., 10.]) 

    def get_reward(self):
        """Uses current pose of sim to return reward."""
        self.dimension_weights = np.array([1, 1., 0.]) #weights for each velocity axis (wieght of z is set to zero as to not penalize upwards velocities)
        vel_vector = self.sim.v 
        distance = np.multiply(vel_vector, self.dimension_weights)/np.linalg.norm(self.dimension_weights) #scale velocities according to weights
        
        reward = 2*(1 - np.tanh(np.linalg.norm(2*distance))**2)-1 #reward function corresponding to a slightly modified derivative of tanh()
                                                                  #returns 1 when in zero, and decays to -1 on both infinities
                                                                  #this alongside the velocity weights, aims to reduce movement on the x-y plane
        reward = reward/3
        reward += (np.clip(self.sim.v[2], -5, 5)/5)*2/3

        # Penalize if the quadcopter crashes
        if self.sim.done and self.sim.runtime > self.sim.time:
            reward = -10
        
        return reward

    def step(self, rotor_speeds):
        """Uses action to obtain next state, reward, done."""
        reward = 0
        pose_all = []
        for _ in range(self.action_repeat):
            done = self.sim.next_timestep(rotor_speeds) # update the sim pose and velocities
            reward += self.get_reward() 
            pose_all.append(self.sim.pose)
        next_state = np.concatenate(pose_all)
        return next_state, reward, done

    def reset(self):
        """Reset the sim to start a new episode."""
        self.sim.reset()
        state = np.concatenate([self.sim.pose] * self.action_repeat) 
        return state