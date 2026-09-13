from source.ScenarioReader import ScenarioReader
import numpy as np

def main():

    import yaml

    file_path = 'networks_configurations.yaml'

    networks_configs = yaml.safe_load(open(file_path))

    # ______________________________
    # Networks Parameters
    # ______________________________

    pn = networks_configs['Fixed_service']
    sn = networks_configs['Dmimo_network']

    # Scenarios reader
    sce_reader = ScenarioReader(pn, sn)


    path_lsg = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/InterNetwork/lsg_parameters/'
    path_H   = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/InterNetwork/H_coeffs/'


    link_types = [
        'pn_term_sn_term',
        'pn_term_sn_stat',
        'pn_stat_sn_stat'
    ]

    data = {}

    for link in link_types:
        data[link] = {
            "lsg_coeffs": np.load(f"{path_lsg}{link}_lsg_coeffs_full.npz", allow_pickle=True)[f"{link}_lsg_coeffs"],
            "K_coeffs":   np.load(f"{path_lsg}{link}_K_coeffs_full.npz",   allow_pickle=True)[f"{link}_K_coeffs"],
            "H_coeffs":   np.load(f"{path_H}{link}_H_coeffs_full.npz",     allow_pickle=True)[f"{link}_H_coeffs"]
        }



    sce_reader.set_cross_channels([

        data["pn_term_sn_term"]["lsg_coeffs"], data["pn_term_sn_stat"]["lsg_coeffs"], data["pn_stat_sn_stat"]["lsg_coeffs"],

        data["pn_term_sn_term"]["K_coeffs"], data["pn_term_sn_stat"]["K_coeffs"], data["pn_stat_sn_stat"]["K_coeffs"],

        data["pn_term_sn_term"]["H_coeffs"], data["pn_term_sn_stat"]["H_coeffs"], data["pn_stat_sn_stat"]["H_coeffs"]

        ])


    path   = '/home/samuelserejosilva/Projetos/sim_scenario/scenarios_storage/DMimo/'

    sn_lsg_coeffs = np.load(path + 'lsg_parameters/lsg_coeffs_full.npz', allow_pickle = True)['lsg_coeffs']
    sn_R_matrices = np.load(path + 'R_matrices/aps_R_matrices_full.npz', allow_pickle = True)['aps_R_matrices']
    sn_H_coeffs = np.load(path + 'H_coeffs/H_coeffs_full.npz', allow_pickle = True)['H_coeffs']

    sce_reader.set_geometry([
        sn_lsg_coeffs, sn_R_matrices, sn_H_coeffs
    ])


    # ______________________________
    # UEs scheduling techniques
    # ______________________________

    # Scheduling techniques
    scheduling_techniques_path = 'source/scheduling/scheduling.py'
    
    # UEs scheduling methods & thresholds
    DMimo_UE_scheduling_techniques = ['IndividualEstimated_INR', 'CumulativeIndividualEstimated_INR']
    DMimo_UE_scheduling_thresholds = [-10, -12.5, -15]

   
    # ______________________________
    # UEs panel selection techniques
    # ______________________________

    panel_selection_path = 'source/scheduling/panel_selection.py'

    # UEs panel selection methods
    #DMimo_panel_selection_techniques = ['TpsAltruisticFromLsfGain', 'TpsRandomic']
    DMimo_panel_selection_techniques = ['TpsSelfishFromChannelGain']
    
    
    uplink_strong_LOS_INR_results = {}
    uplink_weak_LOS_INR_results = {}
    uplink_INR_results = {}
    uplink_num_UEs_results = {}
    uplink_SE_results = {}

    for panel_tech in DMimo_panel_selection_techniques:
        for sched_tech in DMimo_UE_scheduling_techniques:
            for sched_thresh in DMimo_UE_scheduling_thresholds:

                key = panel_tech + ' + ' + sched_tech + ' + ' + str(sched_thresh)

                uplink_strong_LOS_INR_results[key] = []
                uplink_weak_LOS_INR_results[key] = []
                uplink_INR_results[key] = []
                uplink_num_UEs_results[key] = []
                uplink_SE_results[key] = []


    num_snapshots = networks_configs['num_snapshots']

    for ite in range(num_snapshots):

        print("Iteration number " + str(ite + 1))

        # Uplink

        for panel_tech in DMimo_panel_selection_techniques:
            sce_reader.set_panel_selection_technique(panel_selection_path, panel_tech)

            for sched_tech in DMimo_UE_scheduling_techniques:
                for sched_thresh in DMimo_UE_scheduling_thresholds:

                    sce_reader.set_terminal_scheduling_technique(scheduling_techniques_path, sched_tech, sched_thresh)

                    key = panel_tech + ' + ' + sched_tech + ' + ' + str(sched_thresh)

                    print(key)

                    (ul_caused_inr, 
                     ul_num_UEs, 
                     ul_sum_se ) = sce_reader.compute_uplink_kpis_for_panel_selection_and_scheduling(ite)

                    uplink_INR_results[key].append(ul_caused_inr)
                    uplink_num_UEs_results[key].append(ul_num_UEs)
                    uplink_SE_results[key].append(ul_sum_se)



    import pandas as pd

    ul_inr_strong_df = pd.DataFrame(uplink_strong_LOS_INR_results)
    ul_inr_weak_df  = pd.DataFrame(uplink_weak_LOS_INR_results)

    ul_inr_df = pd.DataFrame(uplink_INR_results)
    ul_num_UEs_df = pd.DataFrame(uplink_num_UEs_results)
    ul_se_df = pd.DataFrame(uplink_SE_results)

    path_inr = 'results_storage/inr_results/'
    path_num = 'results_storage/num_ues_results/'
    path_se = 'results_storage/se_results/'

    ul_inr_strong_df.to_csv(path_inr + 'ul_inr_strong.csv', index=False, sep=',', encoding='utf-8')
    ul_inr_weak_df.to_csv(path_inr + 'ul_inr_weak.csv', index=False, sep=',', encoding='utf-8')

    ul_inr_df.to_csv(path_inr + 'ul_inr.csv', index=False, sep=',', encoding='utf-8')

    ul_num_UEs_df.to_csv(path_num + 'ul_num_UEs.csv', index=False, sep=',', encoding='utf-8')
    ul_se_df.to_csv(path_se + 'ul_sum_se.csv', index=False, sep=',', encoding='utf-8')
        
    


if __name__ == "__main__":
    main()
