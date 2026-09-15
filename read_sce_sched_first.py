from source.ScenarioReader import ScenarioReader
import numpy as np
import yaml
from pathlib import Path

def main():

    file_path = 'networks_configurations.yaml'
    

    networks_configs = yaml.safe_load(open(file_path))
    
    # 1. Networks Parameters
    pn = networks_configs['Fixed_service']
    sn = networks_configs['Dmimo_network']
    
    # Scenarios reader
    sce_reader = ScenarioReader(pn, sn)


    from read_scenarios import load_inter_network_parameters

    inter_net_data = load_inter_network_parameters()


    sce_reader.set_cross_channels([

    inter_net_data["pn_term_sn_term"]["ls_fading_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_fading_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_fading_coeffs"],

    inter_net_data["pn_term_sn_term"]["ls_gain_coeffs"], inter_net_data["pn_term_sn_stat"]["ls_gain_coeffs"], inter_net_data["pn_stat_sn_stat"]["ls_gain_coeffs"],

    inter_net_data["pn_term_sn_term"]["K_coeffs"], inter_net_data["pn_term_sn_stat"]["K_coeffs"], inter_net_data["pn_stat_sn_stat"]["K_coeffs"],

    inter_net_data["pn_term_sn_term"]["H_coeffs"], inter_net_data["pn_term_sn_stat"]["H_coeffs"], inter_net_data["pn_stat_sn_stat"]["H_coeffs"]

        ])

    dir_path = Path(__file__).resolve().parent

    path   = str(dir_path) + '/scenarios_storage/DMimo/'

    sn_lsg_coeffs = np.load(path + 'lsg_parameters/lsg_coeffs_full.npz', allow_pickle = True)['lsg_coeffs']
    sn_R_matrices = np.load(path + 'R_matrices/aps_R_matrices_full.npz', allow_pickle = True)['aps_R_matrices']
    sn_H_coeffs = np.load(path + 'H_coeffs/H_coeffs_full.npz', allow_pickle = True)['H_coeffs']

    sce_reader.set_geometry([
        sn_lsg_coeffs, sn_R_matrices, sn_H_coeffs
    ])
    



    scheduling_techniques_path = 'source/scheduling/scheduling.py'
    panel_selection_path = 'source/scheduling/panel_selection.py'
       
    # UEs scheduling methods & thresholds
    DMimo_UE_scheduling_techniques = ["IndividualEstimated_INR",]
    DMimo_UE_scheduling_thresholds = [-10]

    # UEs panel selection methods
    DMimo_panel_selection_techniques = ['TpsAltruisticFromLsfGain', 'TpsRandomic']

    DMimo_UE_scheduling_methods_names = ["min_antenna_gain_as_first_step", "max_antenna_gain_as_first_step",]

    # 1. Panel selection before scheduling
    ul_inr_results = {}
    ul_num_ues_results = {}
    ul_sum_se_results  = {}

    # Panel selection technique
    for panel_tech in DMimo_panel_selection_techniques:
        # Scheduling technique
        for sched_tech in DMimo_UE_scheduling_techniques:
            # Scheduling threshold
            for sched_thresh in DMimo_UE_scheduling_thresholds:
                # Scheduling method name
                for meth_name in DMimo_UE_scheduling_methods_names:

                    key = sched_tech + " + " + meth_name + " + " + str(sched_thresh) + " + " + panel_tech

                    print(key)

                    ul_inr_results[key]     = []
                    ul_num_ues_results[key] = []
                    ul_sum_se_results[key]  = []

    num_snapshots = networks_configs['num_snapshots']

    for ite in range(num_snapshots):
    
        print("Iteration number " + str(ite + 1))
        # Panel selection technique
        for panel_tech in DMimo_panel_selection_techniques:
            sce_reader.set_panel_selection_technique(panel_selection_path, panel_tech)

            # Scheduling technique
            for sched_tech in DMimo_UE_scheduling_techniques:
                # Scheduling threshold
                for sched_thresh in DMimo_UE_scheduling_thresholds:
                    # Scheduling method name
                    for meth_name in DMimo_UE_scheduling_methods_names:

                        sce_reader.set_terminal_scheduling_technique(
                            scheduling_techniques_path, sched_tech, meth_name, sched_thresh)

                        key = sched_tech + " + " + meth_name + " + " + str(sched_thresh) + " + " + panel_tech

                        (
                        ul_caused_inr, 
                        ul_num_ues, 
                        ul_sum_se) = sce_reader.compute_uplink_kpis_for_scheduling_first(ite)


                        ul_inr_results[key].append(ul_caused_inr)
                        ul_num_ues_results[key].append(ul_num_ues)
                        ul_sum_se_results[key].append(ul_sum_se)  


if __name__ == "__main__":
    main()
