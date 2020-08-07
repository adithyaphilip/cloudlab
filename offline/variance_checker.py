import offline.metric_calc as metric_calc
import offline.log_plotter as log_plotter
import os
import sys
import multiprocessing as mp
from typing import List
import pandas as pd
import numpy as np

BTL_LINK = 1280  # mega BYTES
THREADS = 10


def investigate_early_flows(df: pd.DataFrame):
    a_df = df.drop_duplicates(['ip', 'socket'])[['ip', 'socket']]
    a_df2 = log_plotter.trim_flow_times(1200, 0, df)
    a_df2 = a_df2.drop_duplicates(['ip', 'socket'])[['ip', 'socket']]
    # a_df3[]
    pass


def calc_jfi(df):
    df = log_plotter.trim_flow_times(log_plotter.TIME_S_TRIM_START, log_plotter.TIME_S_TRIM_END, df)
    bws = log_plotter.get_avg_gprs(df, False)
    return metric_calc.get_jfi(bws)


def get_avg_bw_by_rtt(id_tup_df_trimmed):
    return id_tup_df_trimmed[0], log_plotter.get_bw_by_rtt(id_tup_df_trimmed[1],
                                                           id_tup_df_trimmed[0][log_plotter.IND_TYPE2_COUNT],
                                                           id_tup_df_trimmed[0][log_plotter.IND_NUM_NODES],
                                                           False)


def main():
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [(10, 5000, 600, 'reno', 22, 0, 0, trial) for trial in range(1, 2)]
    # (15, 800, 600, 'cubic', 20, 0, 0, 50),
    # (10, 6000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 4000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 200, 600, 'cubic', 20, 0, 0, 50),
    # (2, 1500, 600, 'cubic', 20, 0, 0, 50)]

    dfs_demands = log_plotter.get_dfs_and_demands(BTL_LINK,
                                                  nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    # investigate_early_flows(dfs_demands[0][0])

    pool = mp.Pool(THREADS)
    bws = pool.map(get_avg_bw_by_rtt, list(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l,
                                               map(lambda x: log_plotter.trim_flow_times(log_plotter.TIME_S_TRIM_START,
                                                                                         log_plotter.TIME_S_TRIM_END,
                                                                                         x[0]),
                                                   dfs_demands))))
    with open('../results/bws/bw_result', "w") as f:
        f.writelines(map(lambda x: str(x) + '\n', bws))

    jfis = pool.map(calc_jfi, list(map(lambda x: x[0], dfs_demands)))

    print("Finished!")

    # with open('../results/jfis/%d_nodes_%d_flows_%d_s_%s_algo_rev_%d_nm1_%d_nm2_%d_delayed_%d' %
    #           nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l[0], "w") as f:
    #     f.writelines(map(lambda x: str(x) + '\n', jfis))
    with open('../results/jfis/jfi_10000', "w") as f:
        f.writelines(map(lambda x: str(x) + '\n', jfis))


if __name__ == '__main__':
    main()
