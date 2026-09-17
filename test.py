import numpy as np

from source.physical.channel import RicianChannel

Rice = RicianChannel()


### Here i want o test the "generate_channels" func


num_rx = 1
num_tx = 1

num_rx_pan = 1
num_tx_pan = 1

rx_N_h = 3
rx_N_v = 2
rx_N = rx_N_h * rx_N_v

tx_N_h = 1
tx_N_v = 2
tx_N = tx_N_h * tx_N_v



ls_shape = (num_rx, num_tx, num_rx_pan, num_tx_pan)

ls_gains = np.random.uniform(0,1, size = ls_shape)

K_facs = np.random.uniform(0,1, size = (num_rx, num_tx))

rx_h_aoas = np.random.uniform(0,1, size = ls_shape)
rx_v_aoas = np.random.uniform(0,1, size = ls_shape)

rx_aoas = (rx_h_aoas, rx_v_aoas)

tx_h_aoas = np.random.uniform(0,1, size = ls_shape)
tx_h_aoas = tx_h_aoas.transpose(1,0,3,2)
tx_v_aoas = np.random.uniform(0,1, size = ls_shape)
tx_v_aoas = tx_v_aoas.transpose(1,0,3,2)

tx_aoas = (tx_h_aoas, tx_v_aoas)


rx_R_matrices = np.random.uniform(size = (*ls_shape, rx_N, rx_N))

tx_R_matrices = np.random.uniform(size = (*ls_shape, tx_N, tx_N))
tx_R_matrices = tx_R_matrices.transpose(1,0,3,2, 4, 5)


rng = np.random.default_rng(seed=123)

rx_N = (rx_N_h, rx_N_v)
tx_N = (tx_N_h, tx_N_v)

H1 = Rice.generate_multiple_channels_2(ls_gains, K_facs, rx_R_matrices, tx_R_matrices, rx_aoas, tx_aoas, rx_N, tx_N, rng)

H2 = Rice.generate_multiple_channels(ls_gains, K_facs, rx_R_matrices, tx_R_matrices, *rx_aoas, *tx_aoas, *rx_N, *tx_N, rng)

print(H1)

print(H2)

# ls_gain_coeffs, K_coeffs,
#                                    R_rx_matrices, R_tx_matrices,
#                                    doas_rx: tuple, doas_tx: tuple,
#                                    N_rx: tuple, N_tx: tuple,
#                                    rng: object