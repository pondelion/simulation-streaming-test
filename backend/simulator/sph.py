from copy import copy
from typing import Dict, List

import numpy as np


class Poly6Kernel:

    def __init__(self, h: float):
        self._h = h
        self._alpha = 4.0 / (np.pi * np.power(h, 8))
    
    def kernel(self, distances: np.ndarray):
        ks = np.zeros(len(distances))
        filt = np.where(distances < self._h)[0]
        if len(filt) > 0:
            ks[filt] = self._alpha * np.power(self._h**2 - distances[filt]**2, 3)
        return ks

    def gradient(self, rvs: np.ndarray):
        grad_vecs = np.zeros_like(rvs)
        distances = np.sqrt((rvs**2).sum(axis=1))
        filt = np.where(distances < self._h)[0]
        if len(filt) > 0:
            c = -6.0 * self._alpha * np.power(self._h**2 - distances[filt]**2, 2)
            grad_vecs[filt] = c.reshape(-1, 1) * rvs[filt]
        return grad_vecs


class SPHSystem:

    def __init__(self, n_particles: int):
        self._n_particles = n_particles
        self._x_min = -1
        self._x_max = 1
        self._z_min = -1
        self._z_max = 1
        self._y_min = 0
        self._effective_r = 0.1
        self._poly6kernel = Poly6Kernel(h=self._effective_r*3.5)
        self._density_base = 300
        self._stiffness = 100.0
        self._viscosity = 1
        self._gravity = np.array([0.0, -9.8, 0.0])
        self.init()

    def init(self):
        self._t = 0.0
        # positions
        self._ps = np.zeros((self._n_particles, 3))
        self._ps[:, 0] = np.random.uniform(self._x_min, high=0, size=self._n_particles)  # x
        self._ps[:, 1] = np.random.uniform(self._y_min, high=5, size=self._n_particles)  # y
        self._ps[:, 2] = np.random.uniform(self._z_min, high=0, size=self._n_particles)  # z
        # velocities
        self._vs = np.zeros((self._n_particles, 3))
        self._vs2 = np.zeros((self._n_particles, 3))
        # densities
        self._densities = np.ones(self._n_particles) * self._density_base
        # pressures
        self._pressures = np.ones(self._n_particles)
        # mass
        self._masses = np.ones(self._n_particles)
        # force
        self._forces = np.zeros((self._n_particles, 3))

    def update(self, dt: float) -> None:
        self._t += dt
        gridid_particle_mappings = self.split_particles_to_grids()
        # update density and pressure
        for (x_grid_idx, y_grid_idx, z_gird_idx), particle_ids in gridid_particle_mappings.items():
            for particle_id in particle_ids:
                neighboring_particle_ids = self.get_neighboring_particles(
                    particle_id, x_grid_idx, y_grid_idx, z_gird_idx, gridid_particle_mappings
                )
                # print(f'{particle_id} : {neighboring_particle_ids}')
                rvs = - self._ps[neighboring_particle_ids] + self._ps[particle_id]
                distances = np.sqrt((rvs**2).sum(axis=1))
                density, pressure = self.calc_density_pressure(particle_id, neighboring_particle_ids, distances)
                self._densities[particle_id] = density
                self._pressures[particle_id] = pressure
        # update force
        for (x_grid_idx, y_grid_idx, z_gird_idx), particle_ids in gridid_particle_mappings.items():
            for particle_id in particle_ids:
                neighboring_particle_ids = self.get_neighboring_particles(
                    particle_id, x_grid_idx, y_grid_idx, z_gird_idx, gridid_particle_mappings
                )
                if len(neighboring_particle_ids) > 0:
                    rvs = - self._ps[neighboring_particle_ids] + self._ps[particle_id]
                    distances = np.sqrt((rvs**2).sum(axis=1))
                    f = self.calc_interactive_force(particle_id, neighboring_particle_ids, rvs, distances)
                    f += self.calc_external_force(particle_id)
                else:
                    f = self.calc_external_force(particle_id)
                self._forces[particle_id] = f
        self._forces = np.clip(self._forces, -50, 50)
        # self._forces -= 0.2 * np.clip(self._vs, -100000, 100000) ** 2

        # update velocity and positions
        self._vs2 += dt * self._forces
        self._ps += dt * self._vs2
        self._vs = self._vs2 + 0.5 * dt * self._forces
        ref_coef = 0.7
        y_filt = np.where((self._ps[:, 1] < self._y_min) | (self._ps[:, 1] > 3))[0]
        if len(y_filt) > 0:
            self._vs[y_filt, 1] = -ref_coef*self._vs[y_filt, 1]
            self._vs2[y_filt, 1] = -ref_coef*self._vs2[y_filt, 1]
        x_filt = np.where((self._ps[:, 0] < self._x_min) | (self._ps[:, 0] > self._x_max))[0]
        if len(x_filt) > 0:
            self._vs[x_filt, 0] = -ref_coef*self._vs[x_filt, 0]
            self._vs2[x_filt, 0] = -ref_coef*self._vs2[x_filt, 0]
        z_filt = np.where((self._ps[:, 2] < self._z_min) | (self._ps[:, 2] > self._z_max))[0]
        if len(z_filt) > 0:
            self._vs[z_filt, 2] = -ref_coef*self._vs[z_filt, 2]
            self._vs2[z_filt, 2] = -ref_coef*self._vs2[z_filt, 2]
        self._vs += 0.00001*np.random.randn(self._n_particles, 3)
        self._ps[:, 0] = np.clip(self._ps[:, 0], self._x_min, self._x_max)
        self._ps[:, 1] = np.clip(self._ps[:, 1], self._y_min, 3)
        self._ps[:, 2] = np.clip(self._ps[:, 2], self._z_min, self._z_max)

    def split_particles_to_grids(self):
        self._gridid_particle_mappings = {}
        x_grid_indices = (self._ps[:, 0] - self._x_min) // self._effective_r
        y_grid_indices = (self._ps[:, 1] - self._y_min) // self._effective_r
        z_grid_indices = (self._ps[:, 2] - self._z_min) // self._effective_r
        for particle_id, (x_grid_idx, y_grid_idx, z_gird_idx) in enumerate(zip(x_grid_indices, y_grid_indices, z_grid_indices)):
            if (x_grid_idx, y_grid_idx, z_gird_idx) not in self._gridid_particle_mappings:
                self._gridid_particle_mappings[(x_grid_idx, y_grid_idx, z_gird_idx)] = [particle_id]
            else:
                self._gridid_particle_mappings[(x_grid_idx, y_grid_idx, z_gird_idx)].append(particle_id)
        return self._gridid_particle_mappings

    def get_neighboring_particles(self, particle_id, x_grid_idx, y_grid_idx, z_gird_idx, gridid_particle_mappings):
        particles = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if (x_grid_idx+dx, y_grid_idx+dy, z_gird_idx+dz) in gridid_particle_mappings:
                        particles += gridid_particle_mappings[(x_grid_idx+dx, y_grid_idx+dy, z_gird_idx+dz)]
        particles.remove(particle_id)
        return particles

    def calc_density_pressure(
        self,
        tartget_particle_id: int,
        neighboring_particle_ids: List[int],
        # rvs: np.ndarray,
        distances: np.ndarray,
    ):
        if len(neighboring_particle_ids) == 0:
            # density = pressure = 0.0
            density = self._density_base
            pressure = 0.0
        else:
            density = (self._poly6kernel.kernel(distances) * self._masses[neighboring_particle_ids]).sum()
            pressure = max(0, self._stiffness * (density - self._density_base))
        return density, pressure

    def calc_interactive_force(
        self,
        tartget_particle_id: int,
        neighboring_particle_ids: List[int],
        rvs: np.ndarray,
        distances: np.ndarray,
    ):
        npi = neighboring_particle_ids
        tpi = tartget_particle_id
        # pressure
        grads = self._poly6kernel.gradient(rvs)  # size=(n_neighboring_particles, 3)
        # print(f'{self._densities[npi]**2} : {self._densities[tpi]**2}')
        f = -self._masses[npi] * (self._pressures[npi] / (self._densities[npi]**2) + self._pressures[tpi] / (self._densities[tpi]**2))  # (n_particles)
        f = grads * f.reshape(-1, 1)  # size=(n_neighboring_particles, 3)

        # viscosity
        r2 = distances**2  # size=(n_neighboring_particles)
        dv = self._vs[tpi] - self._vs[npi]  # size=(n_neighboring_particles, 3)
        fv = self._masses[tpi] * 2 * self._viscosity  / (self._densities[npi] * self._densities[tpi]) / np.clip(r2, 0.0001, None)  # size=(n_neighboring_particles)
        f += fv.reshape(-1, 1) * dv  # size=(n_neighboring_particles, 3)
        
        # # gravity
        # f += self._gravity.reshape(1, 3)  # size=(n_neighboring_particles, 3)

        f = f.sum(axis=0)  # size=(n_neighboring_particles, 3) => (3)

        return f

    def calc_external_force(self, tartget_particle_id):
        f = self._gravity
        return f

    def get_states(self) -> Dict:
        return {
            'time': self._t,
            'positions': self._ps.reshape((-1, 3)).tolist(),
            # 'velocities': self._vs.tolist(),
        }
