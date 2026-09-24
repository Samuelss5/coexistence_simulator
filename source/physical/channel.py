import numpy as np

class RicianChannelModel:

    """
    
    
    """

    @classmethod
    def generate_multiple_channels(cls, 
                                   ls_gain_coeffs, K_coeffs,
                                   receive_R_matrices, transmi_R_matrices,
                                   receive_doas: tuple, transmi_doas: tuple,
                                   receive_N: tuple, transmi_N: tuple,
                                   rng: object):

        (
        n_receive, 
        n_transmi, 
        n_receive_panel, 
        n_transmi_panel) = ls_gain_coeffs.shape     

        # Receiver num of antennas indexes (H and V)
        receive_N_horz_arange = np.arange(0, receive_N[0])
        receive_N_vert_arange = np.arange(0, receive_N[1])

        # Receiver total num of antennas
        receive_N_tot = receive_N[0] * receive_N[1]
        
        # Transmitter num of antennas indexes (H and V)
        transmi_N_horz_arange = np.arange(0, transmi_N[0])
        transmi_N_vert_arange = np.arange(0, transmi_N[1])

        # Receiver total num of antennas
        transmi_N_tot = transmi_N[0] * transmi_N[1]


        shape_of_H = (
            n_receive, 
            n_transmi, 
            n_receive_panel, 
            n_transmi_panel,
            receive_N_tot, 
            transmi_N_tot
         )

        H_coeffs = np.zeros(shape_of_H, dtype=np.complex128)
        
        for rece_id in range(n_receive):
            for tran_id in range(n_transmi):
                for rece_panel_id in range(n_receive_panel):
                    for tran_panel_id in range(n_transmi_panel):
                    
                        receive_horz_af = np.exp(
                        1j * np.pi * receive_N_horz_arange * np.sin(receive_doas[0][rece_id, tran_id, rece_panel_id, tran_panel_id]) * np.cos(receive_doas[1][rece_id, tran_id, rece_panel_id, tran_panel_id])
                        )
                        
                        receive_vert_af = np.exp(
                        1j * np.pi * receive_N_vert_arange * np.cos(receive_doas[1][rece_id, tran_id, rece_panel_id, tran_panel_id])
                        )
                        
                        receive_af = np.kron(receive_horz_af, receive_vert_af)[:, np.newaxis]
                        
                        transmi_horz_af = np.exp(
                        1j * np.pi * transmi_N_horz_arange * np.sin(transmi_doas[0][tran_id, rece_id, tran_panel_id, rece_panel_id]) * np.cos(transmi_doas[1][tran_id, rece_id, tran_panel_id, rece_panel_id])
                        )
                        
                        transmi_vert_af = np.exp(
                        1j * np.pi * transmi_N_vert_arange * np.cos(transmi_doas[1][tran_id, rece_id, tran_panel_id, rece_panel_id])
                        )
                        
                        transmi_af = np.kron(transmi_horz_af, transmi_vert_af)[:, np.newaxis]
                        
                        steering_matrix = receive_af @ transmi_af.T
                        
                        diff = rng.normal(0,1, size=steering_matrix.shape) + 1j * rng.normal(0,1, size=steering_matrix.shape)
                        
                        H_nlos = ( np.sqrt(receive_R_matrices[rece_id, tran_id, rece_panel_id, tran_panel_id]) 
                                   @ diff
                                   @ np.sqrt(transmi_R_matrices[tran_id, rece_id, tran_panel_id, rece_panel_id]) ) * np.sqrt(0.5)
                                   
                        K = K_coeffs[rece_id, tran_id]
                        beta = ls_gain_coeffs[rece_id, tran_id, rece_panel_id, tran_panel_id]
                                 
                        los_coeff  = np.sqrt(K / (K + 1))
                        nlos_coeff = np.sqrt(1 / (K + 1))
                    
                        H = np.sqrt(beta) * (los_coeff * steering_matrix + nlos_coeff * diff)
                        
                        H = np.sqrt(beta * 0.5) * diff
                        
                        H_coeffs[rece_id, tran_id, rece_panel_id, tran_panel_id] = H
                                   
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

