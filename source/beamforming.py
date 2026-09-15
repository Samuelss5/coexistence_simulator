import numpy as np
from scipy.linalg import block_diag, solve

### CELL-FREE OR D-MIMO NETWORKS COMBINING AND BEAMFORMING METHODS ###

class DMimoCentralizedMmseCombining:

    @classmethod
    def compute(cls, 
                H_hat_coeffs: np.ndarray, C_error_matrices: np.ndarray, clustering_matrix: np.ndarray, 
                scheduled_ues: np.ndarray, ul_max_power: float, noise_var: float):

        # OBS: We consider that all scheduled UEs transmit with max power

        # L = number of access points (APs) x number of arrays per AP
        # K = number of user equipments (UEs)
        # Ns = number of antennas at each AP panel/array
        # Nt = number of antennas at each UE panel/array
        L, K, Ns, Nt = H_hat_coeffs.shape

        LNs = L * Ns

        # Power allocation
        transmit_powers_vec = np.zeros(K, dtype=float)
        transmit_powers_vec[scheduled_ues] = ul_max_power
        
        D_matrixes = np.zeros((K, LNs, LNs), dtype = np.complex128)

        for ue_k in range(K):
            D_k = []
            for ap_l in range(L):
                if clustering_matrix[ue_k, ap_l] == 0:
                    D_k.append(np.eye(Ns) * 0)
                elif clustering_matrix[ue_k, ap_l] == 1:
                    D_k.append(np.eye(Ns))

            D_k = block_diag(*D_k)
            D_matrixes[ue_k] = D_k
        
        # Pre-compute all concatenated channels
        H_concatenated = np.zeros((K, LNs, Nt), dtype=np.complex128)

        for ue_j in range(K):
            if transmit_powers_vec[ue_j] > 10**-6:  # Only compute for UEs with non-negligible power

                H_concatenated[ue_j] = np.concatenate(
                    H_hat_coeffs[:, ue_j, :, :], axis=0
                )
            else:
                pass


        C_block = np.zeros((K, LNs, LNs), dtype=np.complex128)

        for ue_k in range(K):
            if transmit_powers_vec[ue_k] > 10e-6:
                C_list = [C_error_matrices[ue_k, ap_l] for sp_l in range(L)]
                C_block[ue_k] = block_diag(*C_list)


        Noise_eye = np.eye(LNs, dtype=np.complex128) * noise_var



        combining_vecs = np.zeros((K,LNs, Nt), dtype=np.complex128)

        for ue_k in range(K):
            if transmit_powers_vec[ue_k] > 10e-6:

                Q_k = np.zeros((LNs, LNs), dtype=np.complex128)

                D_k = D_matrixes[ue_k]

                for ue_j in range(K):
                    if transmit_powers_vec[ue_j] > 10e-6:
                        HH = H_concatenated[ue_j] @ H_concatenated[ue_j].T.conj()
                        Q_k += transmit_powers_vec[ue_j] * D_k @ (HH + C_block[ue_j]) @ D_k
        
                Q_k += Noise_eye

                H_k = H_concatenated[ue_k]
                V_k = transmit_powers_vec[ue_k] * solve(Q_k, D_k @ H_k)
                combining_vecs[ue_k] = V_k
            else:
                combining_vecs[ue_k] = np.zeros((LNs, Nt), dtype=np.complex128)

        return combining_vecs


class DMimoCentralizedMmseBeamforming:

    @classmethod
    def compute(cls, H_est_ul, scheduled_ues, C_matrixes, clustering_matrix, ul_max_power, dl_max_power, noise_var):

        # OBS: We consider that all scheduled UEs transmit with max power

        # L = number of access points (APs) x number of arrays per AP
        # K = number of user equipments (UEs)
        # Ns = number of antennas at each AP panel/array
        # Nt = number of antennas at each UE panel/array
        L, K, Ns, Nt = H_est_ul.shape

        # Each AP can allocate this power to each UE
        power_alloc = dl_max_power / K



        LNs = L * Ns

        # Power allocation
        transmit_powers_vec = np.zeros(K, dtype=float)
        transmit_powers_vec[scheduled_ues] = ul_max_power
        
        D_matrixes = np.zeros((K, LNs, LNs), dtype = np.complex128)

        for ue_k in range(K):
            D_k = []
            for ap_l in range(L):
                if clustering_matrix[ue_k, ap_l] == 0:
                    D_k.append(np.eye(Ns) * 0)
                elif clustering_matrix[ue_k, ap_l] == 1:
                    D_k.append(np.eye(Ns))

            D_k = block_diag(*D_k)
            D_matrixes[ue_k] = D_k
        
        # Pre-compute all concatenated channels
        H_concatenated = np.zeros((K, LNs, Nt), dtype=np.complex128)

        for ue_j in range(K):
            if transmit_powers_vec[ue_j] > 10**-6:  # Only compute for UEs with non-negligible power

                H_concatenated[ue_j] = np.concatenate(
                    H_est_ul[:, ue_j, :, :], axis=0
                )
            else:
                pass


        C_block = np.zeros((K, LNs, LNs), dtype=np.complex128)

        for ue_k in range(K):
            if transmit_powers_vec[ue_k] > 10e-6:
                C_list = [C_matrixes[ue_k, ap_l] for sp_l in range(L)]
                C_block[ue_k] = block_diag(*C_list)


        Noise_eye = np.eye(LNs, dtype=np.complex128) * noise_var



        combining_vecs = np.zeros((K,LNs, Nt), dtype=np.complex128)

        for ue_k in range(K):
            if transmit_powers_vec[ue_k] > 10e-6:

                Q_k = np.zeros((LNs, LNs), dtype=np.complex128)

                D_k = D_matrixes[ue_k]

                for ue_j in range(K):
                    if transmit_powers_vec[ue_j] > 10e-6:
                        HH = H_concatenated[ue_j] @ H_concatenated[ue_j].T.conj()
                        Q_k += transmit_powers_vec[ue_j] * D_k @ (HH + C_block[ue_j]) @ D_k
        
                Q_k += Noise_eye

                H_k = H_concatenated[ue_k]
                V_k = transmit_powers_vec[ue_k] * solve(Q_k, D_k @ H_k)
                combining_vecs[ue_k] = V_k
            else:
                combining_vecs[ue_k] = np.zeros((LNs, Nt), dtype=np.complex128)

        
        precoding_vectors = np.zeros((K, LNs, Nt), dtype=np.complex128)
        for ue_k in range(K):
            v_k = combining_vecs[ue_k]

            w_k = np.sqrt(power_alloc * L) * v_k / np.linalg.norm(v_k) 

            precoding_vectors[ue_k] = w_k

        return precoding_vectors
    


        
        


class NoCombining:
    @classmethod
    def compute(cls, num_receivers, num_antennas):
        return np.ones((num_receivers, num_antennas))

class NoBeamforming:
    @classmethod
    def compute(cls, num_transmitters, num_antennas):
        return np.ones((num_transmitters, num_antennas))




### FIXED-SERVICES METHODS ###

# Since both fixed receivers and transmitters are equipped with a single plate antenna, there is not a real combining or beamforming

# class FixedReceiver_combining:

#     @classmethod
#     def compute(cls, num_receivers, num_antennas):

#         return np.ones((num_receivers, num_antennas))


# class FixedTransmitter_beamforming:

#     @classmethod
#     def compute(cls, num_transmitters, num_antennas):

#         return np.ones((num_transmitters, num_antennas))


