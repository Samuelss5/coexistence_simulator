import numpy as np

from scipy.linalg import block_diag


def check_signal_type(signal):

    answer = None
    if np.isscalar(signal) or np.ndim(signal) == 0:
        answer = 0.0
    else:
        answer = np.linalg.norm(signal)**2
        
    return answer


class InterNetInterf:

    """
    Class with generic inter network interference functions -> Works for both uplink and downlink scenarios with descentralized combining/precoding techniques
    
    """

    # Uplink to Downlink
    @classmethod
    def uplink_to_downlink(cls,
        channel_tensor,
        sched_term,
        term_sel_panels,
        max_ul_p: float):

        print(channel_tensor.shape)

        num_receivers, num_transmitters, _, _, _, _ = channel_tensor.shape
        
        received_interference = np.zeros(num_receivers, dtype=float)

        for rx_j in range(num_receivers):
            
            interf_j = 0.0

            for tx_k in sched_term:
                
                sp_k = term_sel_panels[tx_k]

                h = channel_tensor[rx_j, tx_k, :, sp_k]
                
                interf_j += np.sqrt(max_ul_p) * h

            received_interference[rx_j] = np.linalg.norm(interf_j)**2


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
                interference_signals[ue_k] = np.linalg.norm(intf_k)**2
        
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
        ul_max_power
    ):
        
        h_dense = np.array(channel_tensor.tolist())
    
        (
        n_ue,
        n_ap,
        n_panel_per_ue,
        n_array_per_ap,
        n_elem_panel,
        n_elem_array
        ) = h_dense.shape
        
        
        n_ap_array = n_ap * n_array_per_ap
        
        # Uplink channel tensor
        h_ul = np.zeros((n_ue, n_ap_array, n_elem_array, n_elem_panel), dtype=np.complex128)

        for ue_id in scheduled_ues:
        
            panel_id = ues_panels[ue_id]

            # shape -> (n_ap, n_array_per_ap, n_elem_array, n_elem_panel)
            h_ue = h_dense[ue_id, :, panel_id]
            h_ue = h_ue.transpose(0, 1, 3, 2)
            h_ue = h_ue.reshape(n_ap_array, n_elem_array, n_elem_panel)

            h_ul[ue_id] = h_ue

        target_signals = np.zeros(n_ue, dtype=float) 
        
        diag_n_elem_array = np.eye(n_elem_array)

        for ue_id in scheduled_ues:
        
            ue_clustering_vec = clustering_matrix[ue_id]
            d_ue = np.kron(np.diag(ue_clustering_vec), diag_n_elem_array)
            
            ue_combiner = combining_vectors[ue_id]
            
            h_ue = np.concatenate( h_ul[ue_id], axis = 0 )
            
            target_signals[ue_id] = ul_max_power * np.linalg.norm( ue_combiner.T.conj() @ d_ue @ h_ue )**2

        return target_signals

    @classmethod
    def uplink_intra_interference(
        cls,
        channel_tensor,
        clustering_matrix,
        scheduled_ues,
        ues_panels,
        combining_vectors,
        ul_max_power
    ):

        h_dense = np.array(channel_tensor.tolist())
        
        # OBS: evite escrever variáveis que se diferenciam apenas pelo prefixo
        
        (
        n_ue,
        n_ap,
        n_panel_per_ue,
        n_array_per_ap,
        n_elem_panel,
        n_elem_array
        ) = h_dense.shape
        
        n_ap_array = n_ap * n_array_per_ap
                

        # Uplink channel tensor
        h_ul = np.zeros((n_ue, n_ap_array, n_elem_array, n_elem_panel), dtype=np.complex128)

        for ue_id in scheduled_ues:
        
            panel_id = ues_panels[ue_id]

            # shape -> (n_ap, n_array_per_ap, n_elem_array, n_elem_panel)
            h_ue = h_dense[ue_id, :, panel_id]
            h_ue = h_ue.transpose(0, 1, 3, 2)
            h_ue = h_ue.reshape(n_ap_array, n_elem_array, n_elem_panel)

            h_ul[ue_id] = h_ue
        

        # vector that will store the desired signals power
        interference_signals = np.zeros(n_ue, dtype=float)
        
        diag_n_elem_array = np.eye(n_elem_array)
        
        for victim_id in scheduled_ues:
        
            victim_clustering_vec = clustering_matrix[victim_id]
            d_victim = np.kron(np.diag(victim_clustering_vec), diag_n_elem_array)
            
            victim_combiner = combining_vectors[victim_id]
            
            # Interference
            victim_interf = 0+0j
            
            for interferer_id in scheduled_ues:
                if interferer_id == victim_id:
                    continue # Don't interfer with himself
                    
                h_interferer = np.concatenate( h_ul[interferer_id], axis = 0 )
                
                victim_interf += np.sqrt(ul_max_power) * (victim_combiner.T.conj() @ d_victim @ h_interferer)
                
            interference_signals[victim_id] = np.linalg.norm(victim_interf)**2
        
        return interference_signals

    @classmethod
    def uplink_receiving_noise(
        cls,
        clustering_matrix,
        scheduled_ues,
        combining_vectors,
        noise_variance,
        rng):
        
        (
        n_ue,
        n_ap_array
        ) = clustering_matrix.shape
        
        # Total of ap antennas
        n_elem_ap_array = combining_vectors.shape[1]
        
        n_elem_array = n_elem_ap_array // n_ap_array
        
        diag_n_elem_array = np.eye(n_elem_array)
        
        received_noise_powers = np.zeros(n_ue, dtype=float)

        receivers_noise = rng.normal( size = (n_elem_ap_array,1) ) + 1j * rng.normal( size=(n_elem_ap_array,1) ) 
        receivers_noise = receivers_noise * np.sqrt(noise_variance * 0.5)
        
        print("Noise : ", noise_variance)
        
        for victim_id in scheduled_ues:
        
            victim_clustering_vec = clustering_matrix[victim_id]
            d_victim = np.kron(np.diag(victim_clustering_vec), diag_n_elem_array)
            
            victim_combiner = combining_vectors[victim_id]
            
            victim_noise = victim_combiner.T.conj() @ d_victim @ receivers_noise
            
            received_noise_powers[victim_id] = np.linalg.norm(victim_noise)**2
            
    
        return received_noise_powers

        



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
        
    
