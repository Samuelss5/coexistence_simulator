import numpy as np

class Centralized_MMSE_estimation:

    @classmethod
    def compute(cls, H_coeffs, R_matrices, sel_panels, scheduled_ues,
                    tau_p: int, ul_max_power: float, noise_var: float):

        

        # K = number of user equipments (UEs)
        # S = number of access points (APs)
        # _ = number of panels/arrays per UE
        # A = number of panels/arrays per AP
        K, S, _, A, Nt, Ns = H_coeffs.shape


        # Nt = number of antennas at each UE panel/array
        # Ns = number of antennas at each AP panel/array
        #Nt, Ns = channel_Coefficients[0,0,0,0].shape

        # L   = number of APs arrays
        # LNs = total number of antennas
        L = S * A
        LNs = L * Ns

        H_dense = np.array(H_coeffs.tolist())

        # What to do when scheduled_ues = [] ?

        n_sched = len(scheduled_ues)

        # Pre-compute all concatenated channels
        H_ul = np.zeros((L, K, Ns, Nt), dtype=np.complex128)

        Rs_dense = np.array(R_matrices.tolist())

        R_ul = np.zeros((L, K, Ns, Ns), dtype=np.complex128)

        print("R_dense: ", Rs_dense.shape)

        for k in range(len(scheduled_ues)):
            ue_k_idx = scheduled_ues[k]
            sp_k     = sel_panels[k]    

            # Current shape -> (S, A, Nt, Ns)
            H_k = H_coeffs[ue_k_idx, :, sp_k, :]

            H_k = H_k.transpose(0, 1, 3, 2)
            H_k = H_k.reshape(L, Ns, Nt)

            print("H_k: ", H_k.shape)

            H_ul[:, ue_k_idx, ...] = H_k

            R_ul[:, ue_k_idx, ...] = Rs_dense[:, ue_k_idx, :, sp_k].reshape(L, Ns, Ns)

        print("R_ul: ", R_ul.shape)


        # OBS: It is important to note that we consider that each UE terminal is equipped with a single antenna

        # Power allocation -> the non scheduled UEs will have their powers set to zero, while the scheduled ones will transmit with max power

        transmit_powers_vec = np.zeros(K, dtype=float)
        transmit_powers_vec[scheduled_ues] = ul_max_power


        # Identify
        pilot_allocation_vec = np.full(K, None, dtype = object)

        num_scheduled = len(scheduled_ues)

        if num_scheduled > 0:
            pilot_allocation_vec[scheduled_ues] = np.arange(num_scheduled) % tau_p



        H_estimated = np.zeros(H_ul.shape, dtype = np.complex128)

        C_error_matrixes = np.zeros((K, L, Ns, Ns), dtype = np.complex128)

        for p in range(tau_p):
            
            # UEs sharing the pilot sequence p
            pilot_p_ues_vec = np.where(pilot_allocation_vec == p)[0]

            
            for l in range(L):

                # Pilot signal received by the l-th Station
                Y_l = np.sqrt(ul_max_power * tau_p) * np.sum(H_ul[l, pilot_p_ues_vec], axis = 0)

                Noise_l = np.random.normal(size=Y_l.shape) + 1j * np.random.normal(size=Y_l.shape)

                Y_l += Noise_l * np.sqrt(0.5) * noise_var
                
                Psi_matrix = np.sum(R_ul[l, pilot_p_ues_vec], axis = 0) * tau_p * ul_max_power + np.eye(Ns) * noise_var

                for k in pilot_p_ues_vec:

                    R_kl = R_ul[l, k]

                    R_kl_Psi = R_kl * np.linalg.inv(Psi_matrix)


                    C_kl = R_kl - ul_max_power * tau_p * (R_kl_Psi @ R_kl)

                    C_error_matrixes[k,l] = C_kl

                    # Estimated channel
                    H_kl = np.sqrt(ul_max_power * tau_p) * (R_kl_Psi @ Y_l)

                    H_estimated[l,k] = H_kl 

        return H_estimated, C_error_matrixes

    


                    


    
            
        



