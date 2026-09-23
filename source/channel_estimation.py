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

        for ue_k in scheduled_ues:
            
            sp_k     = sel_panels[ue_k]    

            # Current shape -> (S, A, Nt, Ns)
            H_k = H_coeffs[ue_k, :, sp_k, :]
            
            H_k = H_k.transpose(0, 1, 3, 2)
            H_k = H_k.reshape(L, Ns, Nt)

            H_ul[:, ue_k, ...] = H_k

            R_ul[:, ue_k, ...] = Rs_dense[:, ue_k, :, sp_k].reshape(L, Ns, Ns)



        # OBS: It is important to note that we consider that each UE terminal is equipped with a single antenna

        # Power allocation -> the non scheduled UEs will have their powers set to zero, while the scheduled ones will transmit with max power

        transmit_powers_vec = np.zeros(K, dtype=float)
        transmit_powers_vec[scheduled_ues] = ul_max_power


        # Identify
        pilot_allocation_vec = np.full(K, None, dtype = object)

        num_scheduled = len(scheduled_ues)
        
        if num_scheduled > 0:
            pilot_allocation_vec[scheduled_ues] = np.arange(num_scheduled) % tau_p
            
        print("pilot_allocation_vec: ", pilot_allocation_vec)

        H_estimated = np.zeros(H_ul.shape, dtype = np.complex128)

        C_error_matrixes = np.zeros((K, L, Ns, Ns), dtype = np.complex128)
        
        eyeN = np.eye(Ns)

        for p in range(tau_p):
            
            # UEs sharing the pilot sequence p
            ues_mask = np.where(pilot_allocation_vec == p)[0]
        
            for l in range(L):
            
                yp = np.sqrt(ul_max_power) * tau_p * np.sum(H_ul[l, ues_mask], axis = 0)
                
                PsiInv = ul_max_power * tau_p * np.sum(R_ul[l, ues_mask], axis = 0) + eyeN
                
                Psi_inv_matrix = np.linalg.inv(PsiInv)

                for ue_k in ues_mask:

                    RPsi = R_ul[l, ue_k] @ Psi_inv_matrix

                    C_error_matrixes[ue_k, l] = R_ul[l, ue_k] - ul_max_power * tau_p * (RPsi @ R_ul[l, ue_k])
                    
                    H_estimated[l, ue_k] = np.sqrt(ul_max_power) * (RPsi @ yp)
                    
                    H_estimated[l, ue_k] = H_ul[l, ue_k]
                 
                    

        #print("H_ul")
        #print(H_ul[0, scheduled_ues[0]])
        
        #print("H_estimated")
        #print(H_estimated[0, scheduled_ues[0]])
        
        return H_estimated, C_error_matrixes

    


                    


    
            
        



