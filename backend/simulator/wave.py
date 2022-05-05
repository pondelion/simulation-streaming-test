from typing import Dict

import numpy as np


class Wave2DSystem:

    def __init__(
        self,
        n_grid_x: int,
        n_grid_z: int,
        dx: float,
        dz: float,
    ):
        self._n_grid_x = n_grid_x
        self._n_grid_z = n_grid_z
        self._dx = dx
        self._dz = dz
        self._x_max = 0.5 * n_grid_x * dx
        self._x_min = -0.5 * n_grid_x * dx
        self._z_max = 0.5 * n_grid_z * dz
        self._z_min = -0.5 * n_grid_z * dz
        self.init()

    def init(self):
        # time
        self._t = 0.0
        # positions
        self._ps = np.zeros((self._n_grid_x+1, self._n_grid_z+1, 3))
        for x_idx in range(self._n_grid_x+1):
            for z_idx in range(self._n_grid_z+1):
                self._ps[x_idx, z_idx, 0] = self._x_min + self._dx*x_idx
                self._ps[x_idx, z_idx, 1] = 3.0*np.sin(0.2*self._t+0.03*x_idx + 0.07*z_idx)
                self._ps[x_idx, z_idx, 2] = self._z_min + self._dx*z_idx
        self._ps[0, :, 1] = 0
        self._ps[-1, :, 1] = 0
        self._ps[:, 0, 1] = 0
        self._ps[:, -1, 1] = 0
        self._prev_ps = self._ps.copy()
        # velocities
        self._vs = np.zeros((self._n_grid_x+1, self._n_grid_z+1, 3))

    def update(self, dt: float) -> None:
        self._t += dt
        # self._ps += dt * self._vs
        # for x_idx in range(self._n_grid_x+1):
        #     for z_idx in range(self._n_grid_z+1):
        #         self._ps[x_idx, z_idx, 1] = 3.0*np.sin(0.2*self._t+0.03*x_idx + 0.07*z_idx)
        x_coef = 10*dt**2/self._dx**2
        z_coef = 10*dt**2/self._dz**2
        self._ps[1:-1, 1:-1, 1] = 2.0*self._ps[1:-1, 1:-1, 1] - self._prev_ps[1:-1, 1:-1, 1] \
            + x_coef * (self._ps[:-2, 1:-1, 1] - 2.0*self._ps[1:-1, 1:-1, 1] + self._ps[2:, 1:-1, 1]) \
            + z_coef * (self._ps[1:-1, :-2, 1] - 2.0*self._ps[1:-1, 1:-1, 1] + self._ps[1:-1, 2:, 1])
        self._ps[0, :, 1] = 0
        self._ps[-1, :, 1] = 0
        self._ps[:, 0, 1] = 0
        self._ps[:, -1, 1] = 0
        self._ps[20, 20, 1] = 3.0*np.sin(0.8*self._t)
        self._prev_ps = self._ps.copy()

    def get_states(self) -> Dict:
        return {
            'time': self._t,
            'positions': self._ps.reshape((-1, 3)).tolist(),
            # 'velocities': self._vs.tolist(),
        }

