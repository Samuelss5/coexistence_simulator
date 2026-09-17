import numpy as np

from scipy.integrate import dblquad # type: ignore
from scipy.linalg import toeplitz # type: ignore

import numba # type: ignore

class GaussianSpatialCorrelationModel:


    @classmethod
    def compute_fast_integrals(cls, r_aoas_h: np.ndarray, r_aoas_v: np.ndarray, N_h: int, N_v: int):

        # Angular spread
        asd_h = 15 # degrees
        asd_v = 15 # degrees

        asd_h = asd_h * np.pi / 180
        asd_v = asd_v * np.pi / 180

        aoas_h_inf = r_aoas_h - 20 * asd_h
        aoas_h_sup = r_aoas_h + 20 * asd_h

        aoas_v_inf = r_aoas_v - 20 * asd_v
        aoas_v_sup = r_aoas_v + 20 * asd_v

        N_h_idxs = np.arange(0, N_h)
        N_v_idxs = np.arange(0, N_v)

        num_rx, num_tx, num_rx_panels, num_tx_panels = r_aoas_h.shape

        R_matrices = np.zeros((num_rx, num_tx, num_rx_panels, num_tx_panels, N_h * N_v, N_h * N_v), dtype=np.complex128)

        for rx in range(num_rx):
            for tx in range(num_tx):
                for rx_p in range(num_rx_panels):
                    for tx_p in range(num_tx_panels):

                        h_samples = np.linspace(aoas_h_inf[rx, tx, rx_p, tx_p], aoas_h_sup[rx, tx, rx_p, tx_p], 300)
                        v_samples = np.linspace(aoas_v_inf[rx, tx, rx_p, tx_p], aoas_v_sup[rx, tx, rx_p, tx_p], 300)

                        H, V = np.meshgrid(h_samples, v_samples)

                        pdf =  np.exp(-H**2 / (2*asd_h**2)) * np.exp(-V**2 / (2*asd_v**2))

                        res_h = []
                        for n_h in N_h_idxs:

                            phase_h = np.exp(1j * np.pi * n_h * np.sin(H) * np.cos(V))

                            integrand_grid = phase_h * pdf

                            res = np.trapezoid(np.trapezoid(integrand_grid, v_samples, axis=0), h_samples)
                            res_h.append(res)

                        res_v = []
                        for n_v in N_v_idxs:

                            phase_v = np.exp(1j * np.pi * n_v * np.cos(V))

                            integrand_grid = phase_v * pdf

                            res = np.trapezoid(np.trapezoid(integrand_grid, v_samples, axis=0), h_samples)
                            res_v.append(res)


                        R_h = toeplitz(np.array(res_h))
                        R_v = toeplitz(np.array(res_v))

                        R_h = R_h * (N_h / np.trace(R_h) )
                        R_v = R_v * (N_v / np.trace(R_v) )

                        R_matrices[rx, tx, rx_p, tx_p] = np.kron(R_h, R_v)

        return R_matrices


    @classmethod
    def compute_fast_integrals_for_queue(cls, queue, r_aoas_h: np.ndarray, r_aoas_v: np.ndarray, N_h: int, N_v: int):

        R_matrices = cls.compute_fast_integrals(r_aoas_h, r_aoas_v, N_h, N_v)

        queue.put(R_matrices)









