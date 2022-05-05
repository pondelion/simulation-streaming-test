from typing import Dict
import numpy as np


class IdealGasSystem:

    def __init__(
        self,
        n_particles: int,
        xmin: float = -1.0,
        xmax: float = 1.0,
        ymin: float = -1.0,
        ymax: float = 1.0,
        zmin: float = -1.0,
        zmax: float = 1.0,
    ):
        self._n_particles = n_particles
        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax
        self._zmin = zmin
        self._zmax = zmax
        self.init()

    def init(self):
        # positions
        self._ps = np.zeros((self._n_particles, 3))
        self._ps[:, 0] = np.random.uniform(
            self._xmin, self._xmax, self._n_particles,
        )
        self._ps[:, 1] = np.random.uniform(
            self._ymin, self._ymax, self._n_particles,
        )
        self._ps[:, 2] = np.random.uniform(
            self._zmin, self._zmax, self._n_particles,
        )
        # velocities
        self._vs = 6*np.random.randn(self._n_particles, 3)
        # time
        self._t = 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        self._ps += dt * self._vs
        # x reflection
        particle_indices = np.where(self._ps[:, 0] >= self._xmax)[0]
        self._ps[particle_indices, 0] = self._xmax - (self._ps[particle_indices, 0] - self._xmax)
        self._vs[particle_indices, 0] = -self._vs[particle_indices, 0]
        particle_indices = np.where(self._ps[:, 0] <= self._xmin)[0]
        self._ps[particle_indices, 0] = self._xmin + (self._xmin - self._ps[particle_indices, 0])
        self._vs[particle_indices, 0] = -self._vs[particle_indices, 0]
        # y reflection
        particle_indices = np.where(self._ps[:, 1] >= self._ymax)[0]
        self._ps[particle_indices, 1] = self._ymax - (self._ps[particle_indices, 1] - self._ymax)
        self._vs[particle_indices, 1] = -self._vs[particle_indices, 1]
        particle_indices = np.where(self._ps[:, 1] <= self._ymin)[0]
        self._ps[particle_indices, 1] = self._ymin + (self._ymin - self._ps[particle_indices, 1])
        self._vs[particle_indices, 1] = -self._vs[particle_indices, 1]
        # z reflection
        particle_indices = np.where(self._ps[:, 2] >= self._zmax)[0]
        self._ps[particle_indices, 2] = self._zmax - (self._ps[particle_indices, 2] - self._zmax)
        self._vs[particle_indices, 2] = -self._vs[particle_indices, 2]
        particle_indices = np.where(self._ps[:, 2] <= self._zmin)[0]
        self._ps[particle_indices, 2] = self._zmin + (self._zmin - self._ps[particle_indices, 2])
        self._vs[particle_indices, 2] = -self._vs[particle_indices, 2]

    def get_states(self) -> Dict:
        return {
            'time': self._t,
            'positions': self._ps.tolist(),
            'velocities': self._vs.tolist(),
        }
