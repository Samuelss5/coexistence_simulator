import numpy as np

from scipy.linalg import block_diag



class InterNetInterf:

    """
    Class with generic inter network interference functions -> Works for both uplink and downlink scenarios with descentralized combining/precoding techniques
    
    """

    # Uplink to Downlink
    @classmethod
    def uplink_to_downlink(cls,
        channel_tensor,):

        num_receivers, num_transmitters, _, _ = channel_tensor.shape

        received_interference = np.zeros(num_receivers, dtype=float)

        for rx_j in range(num_receivers):
            
            interf_j = 0.0

            for tx_k in range(num_transmitters):

                h = channel_tensor[rx_j, tx_k]

                interf_j += np.linalg.norm(h)**2

            received_interference[rx_j] = interf_j


        return received_interference

                           
class InterNetInterfForDMimo:

    """
    Class with inter network interference functions for DMimo networks -> Works for both uplink and downlink scenarios with centralized combining/precoding techniques
    """

    @classmethod
    def downlink_to_uplink(
        cls, 
        channel_tensor,
        clustering_matrix,
        scheduled_ues,
        combining_vectors,
        max_dl_power
        ):

        # 1. H is the channel matrix between the APs and the interferer that is in DL


        # Given that the APs in the cell-free network are the ones experiencing interference 
        # while they are in the uplink, it is expected that the dimensions of the H matrix will reflect this


        # OBS: All DL interferers transmit with maximum power


        h_dense = np.array(channel_tensor.tolist())

        I, S, P, A, Ni, Ns = h_dense.shape
        L = S * A
        LNs = L * Ns

        h_trans = h_dense.transpose(1,3,0,2,5,4)

        
        h_ul = h_trans.reshape(L, I, P, Ns, Ni)

        h_ul = h_ul.reshape(L, I * P, Ns, Ni)


        # K = number of UEs
        K = combining_vectors.shape[0]

        # S  = number of APs (stations)
        # I  = number of interferers in DL
        # A  = number of arrays per AP
        # P  = number of panels per interferer 
        # Ns = number of antennas at each AP array
        # Ni = number of antennas at each DL interferer

        

        # Concatenated channels between the DL interferers and all APs of the cell-free network


        interference_signals = np.zeros(K, dtype=float)

        for ue_k in scheduled_ues:

            # Each UE from the cell-free will have a sense of the interference coming from the other network

            v_k = combining_vectors[ue_k]

            d_k = []
            for ap_l in range(L):
                if clustering_matrix[ue_k, ap_l] == 1:
                    d_k.append(np.eye(Ns))
                else:
                    d_k.append(np.zeros((Ns,Ns)))

            d_k = block_diag(*d_k)
        

            intf_k = 0+0j

            for int_j in range(I):

                h_j = np.concatenate(
                    h_ul[:, int_j, ...], axis = 0
                )

                intf_k += np.sqrt(max_dl_power) * (v_k.T.conj() @ d_k @ h_j)


            if np.isscalar(intf_k) or np.ndim(intf_k) == 0:
                interference_signals[ue_k] = 0.0
            else:
                interference_signals[ue_k] = np.linalg.norm(intf_k, 2)
        
        return interference_signals

class DownlinkToDMimoUplinkInterference:

    """ A interferência que a rede Dmimo, em UL, sofre quando a outra está em DL """

    # The 
    # The cell-free network is the secondary -> 


    # This function is unique, given that when a cell-free network is in uplink, it uses joint and centralized combining techniques at the APs; 
    # therefore, a different notation is required.


    # 1. In a cell-free network we refer to the terminals as UEs and to the stations as APs

    @classmethod
    def compute(
        cls, 
        channel_tensor,
        clustering_matrix,
        scheduled_ues,
        combining_vectors,
        max_dl_power
        ):

        # 1. H is the channel matrix between the APs and the interferer that is in DL


        # Given that the APs in the cell-free network are the ones experiencing interference 
        # while they are in the uplink, it is expected that the dimensions of the H matrix will reflect this


        # OBS: All DL interferers transmit with maximum power


        h_dense = np.array(channel_tensor.tolist())

        I, S, P, A, Ni, Ns = h_dense.shape
        L = S * A
        LNs = L * Ns

        h_trans = h_dense.transpose(1,3,0,2,5,4)

        
        h_ul = h_trans.reshape(L, I, P, Ns, Ni)

        h_ul = h_ul.reshape(L, I * P, Ns, Ni)


        # K = number of UEs
        K = combining_vectors.shape[0]

        # S  = number of APs (stations)
        # I  = number of interferers in DL
        # A  = number of arrays per AP
        # P  = number of panels per interferer 
        # Ns = number of antennas at each AP array
        # Ni = number of antennas at each DL interferer

       

        # Concatenated channels between the DL interferers and all APs of the cell-free network


        interference_signals = np.zeros(K, dtype=float)

        for ue_k in scheduled_ues:

            # Each UE from the cell-free will have a sense of the interference coming from the other network

            v_k = combining_vectors[ue_k]

            d_k = []
            for ap_l in range(L):
                if clustering_matrix[ue_k, ap_l] == 1:
                    d_k.append(np.eye(Ns))
                else:
                    d_k.append(np.zeros((Ns,Ns)))

            d_k = block_diag(*d_k)
        

            intf_k = 0+0j

            for int_j in range(I):

                h_j = np.concatenate(
                    h_ul[:, int_j, ...], axis = 0
                )

                intf_k += np.sqrt(max_dl_power) * (v_k.T.conj() @ d_k @ h_j)


            if np.isscalar(intf_k) or np.ndim(intf_k) == 0:
                interference_signals[ue_k] = 0.0
            else:
                interference_signals[ue_k] = np.linalg.norm(intf_k, 2)
        
        return interference_signals
             



class DMimoInternalSignals:

    """ 
    Class that computes the internal signals of a DMimo network 
    """


    @classmethod
    def uplink_target_signal(
        cls,
        channel_tensor,
        clustering_matrix,
        scheduled_ues,
        ues_panels,
        combining_vectors,
        max_ul_power
    ):

        h_dense = np.array(channel_tensor.tolist())

        # Dimensions according to the mathematic notation
        num_ues, num_aps, num_pan, num_arr, N_pan, N_arr = h_dense.shape
        num_aps_arr = num_aps * num_arr

        # Uplink channel tensor
        h_ul = np.zeros((num_aps_arr, num_ues, N_arr, N_pan), dtype=np.complex128)

        for ue_k in scheduled_ues:
            sp_k = ues_panels[ue_k]

            # shape -> (num_aps, num_arr, N_pan, N_arr)
            h_k = h_dense[ue_k, :, sp_k]
            h_k = h_k.transpose(0, 1, 3, 2)
            h_k = h_k.reshape(num_aps_arr, N_arr, N_pan)

            h_ul[:, ue_k] = h_k

        target_signals = np.zeros(num_ues, dtype=float) 

        for ue_k in scheduled_ues:
            
            d_k = []
            for ap_l in range(num_aps_arr):
                if clustering_matrix[ue_k, ap_l] == 1:
                    d_k.append(np.eye(N_arr))
                else:
                    d_k.append(np.zeros((N_arr, N_arr)))
            
            d_k = block_diag(*d_k)

            v_k = combining_vectors[ue_k]

            h_k = np.concatenate(
                h_ul[:, ue_k], axis = 0
            )

            target_signals[ue_k] = np.linalg.norm(
                np.sqrt(max_ul_power) * (v_k.T.conj() @ d_k @ h_k)
            )**2

        return target_signals

    @classmethod
    def uplink_intra_interference(
        cls,
        channel_tensor,
        clustering_matrix,
        scheduled_ues,
        ues_panels,
        combining_vectors,
        max_ul_power
    ):

        h_dense = np.array(channel_tensor.tolist())
                
        # Dimensions according to the mathematic notation
        num_ues, num_aps, num_pan, num_arr, N_pan, N_arr = h_dense.shape
        num_aps_arr = num_aps * num_arr

        # Uplink channel tensor
        h_ul = np.zeros((num_aps_arr, num_ues, N_arr, N_pan), dtype=np.complex128)

        for ue_k in scheduled_ues:
            sp_k = ues_panels[ue_k]

            # shape -> (num_aps, num_arr, N_pan, N_arr)
            h_k = h_dense[ue_k, :, sp_k]
            h_k = h_k.transpose(0, 1, 3, 2)
            h_k = h_k.reshape(num_aps_arr, N_arr, N_pan)

            h_ul[:, ue_k] = h_k
        

        # vector that will store the desired signals power
        interference_signals = np.zeros(num_ues, dtype=float)

        for ue_k in scheduled_ues:

            d_k = []
            for ap_l in range(num_aps_arr):
                if clustering_matrix[ue_k, ap_l] == 1:
                    d_k.append(np.eye(N_arr))
                else:
                    d_k.append(np.zeros((N_arr, N_arr)))
            
            d_k = block_diag(*d_k)

            v_k = combining_vectors[ue_k]

            intf_k = 0+0j

            for ue_j in scheduled_ues:
                if ue_j != ue_k:

                    h_j = np.concatenate(
                        h_ul[:, ue_k], axis = 0
                    )

                    intf_k += np.sqrt(max_ul_power) * (v_k.T.conj() @ d_k @ h_j)

            if np.isscalar(intf_k) or np.ndim(intf_k) == 0:
                interference_signals[ue_k] = 0.0
            else:
                interference_signals[ue_k] = np.linalg.norm(intf_k)**2
    
        return interference_signals

    @classmethod
    def uplink_receiving_noise(
        cls,
        clustering_matrix,
        scheduled_ues,
        combining_vectors,
        noise_variance,
        rng):
        
        K,L = clustering_matrix.shape
        LNs = combining_vectors.shape[1]
        Ns = int(LNs / L)
        

        noise_powers = np.zeros(K, dtype=float)

        n = rng.normal(size=(LNs,1)) + 1j * rng.normal(size=(LNs,1)) 
        n = n * np.sqrt(0.5 * noise_variance)

        for ue_k in scheduled_ues:

            d_k = []
            for ap_l in range(L):
                if clustering_matrix[ue_k, ap_l] == 1:
                    d_k.append(np.eye(Ns))
                else:
                    d_k.append(np.zeros((Ns,Ns)))
            
            d_k = block_diag(*d_k)
            v_k = combining_vectors[ue_k]

            n_k = v_k.T.conj() @ d_k @ n

            noise_powers[ue_k] = np.linalg.norm(n_k)**2
        
        return noise_powers

        



class DMimoDownlinkToDownlinkInterference:

    @classmethod
    def compute(
        cls, 
        channel_tensor,
        precoding_vectors
        ):

        h_dense = np.array(channel_tensor.tolist())

        R, T, A, P, Nr, Nt = h_dense.shape

        # result: (T, I, A, Nr, Nt)

        h_trans = h_dense.transpose(0,2,1,3,4,5)

        h = h_trans.reshape(R*A, T * P, Nr, Nt)


        # Number of UEs of the DMimo network
        num_ues = precoding_vectors.shape[0]

        interference_signals = np.zeros(R*A, dtype=float)

        for r in range(R*A):

            intf_r = 0.0

            for ue_k in range(num_ues):
                h_rk = np.concatenate(h[r].transpose(0,2,1), axis = 0)
                w_k = precoding_vectors[ue_k]

                intf_r += w_k @ h_rk.T.conj()

            
            if np.isscalar(intf_r) or np.ndim(intf_r) == 0:
                interference_signals[r] = 0.0
            else:
                interference_signals[r] = np.linalg.norm(intf_r)**2

        
        return interference_signals


### INTER NETWORK INTERFERENCE CLASSES

class InterfCausedByDMimo:

    @classmethod
    def uplink_interference(cls, 
        H_tensor, 
        sn_sched_term,
        sn_sel_panels,
        sn_ul_precoders,
        pn_dl_combiners,
        sn_max_ul_p
            ):

        """
        The SN is in uplink: terminals [Tx] -> stations [Rx]
        The PN is in downlink: stations [Tx] -> terminals [Tx]

        InterNet interference: SN terminals [TX] -> PN terminals [Rx]
        """

        # OBS: "pan" is the abbreviation for panel 

        H = np.array(H_tensor.tolist())

        num_pn_term, num_sn_term, num_pn_pan, num_sn_pan = H.shape

        pn_interference_received_from_sn_dl = np.zeros(num_pn_term, dtype=np.float64)

        for pn_term_j in range(num_pn_term):

            interf_j = 0.0

            v_j = pn_dl_combiners[pn_term_j]

            for sn_term_k in sn_sched_term:
                sp_k = sn_sel_panels[sn_term_k]
                h = H[pn_term_j, sn_term_k, 0, sp_k]

                w_k = sn_ul_precoders[sn_term_k]

                interf_j += ( v_j.T.conj() @ h @ w_k ) * np.sqrt(sn_max_ul_p)
        
    
        
            if np.isscalar(interf_j) or np.ndim(interf_j) == 0:
                pn_interference_received_from_sn_dl[pn_term_j] = 0.0
            else:
                pn_interference_received_from_sn_dl[pn_term_j] = np.linalg.norm(interf_j)**2

        return pn_interference_received_from_sn_dl
        
    
