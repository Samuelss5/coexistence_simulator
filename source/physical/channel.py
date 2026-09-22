import numpy as np

class RicianChannelModel:

    """
    
    
    """

    # Existe a necessidade de eu reescrever o mesmo código nos dois métodos? 

    @classmethod
    def generate_multiple_channels(cls, 
                                   ls_gain_coeffs, K_coeffs,
                                   rx_R_matrices, tx_R_matrices,
                                   rx_doas: tuple, tx_doas: tuple,
                                   rx_N: tuple, tx_N: tuple,
                                   rng: object):

        # OBS: "num" is number, obviously
        # OBS: "p" is a reduction of panel
        (
        num_rx, 
        num_tx, 
        num_rx_p, 
        num_tx_p) = ls_gain_coeffs.shape     

        # Receiver num of antennas indexes (H and V)
        rx_N_h_arange = np.arange(0, rx_N[0])
        rx_N_v_arange = np.arange(0, rx_N[1])

        # Receiver total num of antennas
        rx_N_tot = rx_N[0] * rx_N[1]
        
        # Transmitter num of antennas indexes (H and V)
        tx_N_h_arange = np.arange(0, tx_N[0])
        tx_N_v_arange = np.arange(0, tx_N[1])

        # Receiver total num of antennas
        tx_N_tot = tx_N[0] * tx_N[1]


        shape_of_H = (
            num_rx, 
            num_tx, 
            num_rx_p, 
            num_tx_p,
            rx_N_tot, tx_N_tot
         )

        H_coeffs = np.zeros(shape_of_H, dtype=np.complex128)

        # For each element of the "doas_rx[0]" tensor we shall have a 1D vector

        # Arrays factors from the receivers (rx) POV (H and V)
        rx_h_arrays_factors = np.exp(
            1j * np.pi * rx_N_h_arange[None, None, None, None, :] * np.sin(rx_doas[0][..., None] ) * np.cos(rx_doas[1][..., None])
            )
        
        rx_v_arrays_factors = np.exp(
            1j * np.pi * rx_N_v_arange * np.cos(rx_doas[1][..., None])
            )

        # Arrays factors from the transmitters (tx) POV (H and V)
        tx_h_arrays_factors = np.exp(
            1j * np.pi * tx_N_h_arange[None, None, None, None, :] * np.sin(tx_doas[0][..., None]) * np.cos(tx_doas[1][..., None])
            )
        tx_v_arrays_factors = np.exp(
            1j * np.pi * tx_N_v_arange[None, None, None, None, :] * np.cos(tx_doas[1][..., None])
            )


        rx_arrays_factors = rx_h_arrays_factors[..., :, None] * rx_v_arrays_factors[..., None, :]

        new_shape = rx_arrays_factors.shape[:-2] + (-1,)
        rx_arrays_factors = rx_arrays_factors.reshape(new_shape)


        tx_arrays_factors = tx_h_arrays_factors[..., :, None] * tx_v_arrays_factors[..., None, :]
        new_shape = tx_arrays_factors.shape[:-2] + (-1,)
        tx_arrays_factors = tx_arrays_factors.reshape(new_shape)
        

        steering_matrices = np.matmul(rx_arrays_factors[..., :, None], tx_arrays_factors[..., None, :].transpose(1,0,3,2,4,5))
        
        diffuses = rng.normal(0,1, size=steering_matrices.shape) + 1j * rng.normal(0,1, size=steering_matrices.shape)
        
        H_nlos = np.sqrt(rx_R_matrices) @ diffuses @ np.sqrt(tx_R_matrices.transpose(1,0,3,2,4,5))

        los_coeffs  = np.sqrt(K_coeffs[..., None, None, None, None] / (K_coeffs[..., None, None, None, None] + 1))
        nlos_coeffs = np.sqrt(1 / (K_coeffs[..., None, None, None, None] + 1))


        H_coeffs = np.sqrt(ls_gain_coeffs[..., None, None] / 2) * (
            los_coeffs * steering_matrices + nlos_coeffs * H_nlos
            )

        

        return H_coeffs



    @classmethod
    def generate_multiple_channels_for_queue(cls,
                                             ls_gain_coeffs, K_coeffs,
                                             R_rx_matrices, R_tx_matrices,
                                             doas_rx: tuple, doas_tx: tuple,
                                             N_rx: tuple, N_tx: tuple,
                                             rng: object,
                                             queue):

        H_coeffs = cls.generate_multiple_channels(
            ls_gain_coeffs, K_coeffs,
            R_rx_matrices, R_tx_matrices,
            doas_rx, doas_tx,
            N_rx, N_tx, 
            rng)
    
        queue.put(H_coeffs)

