import offline.metric_calc as metric_calc
import offline.log_plotter as log_plotter
import os
import sys
import multiprocessing as mp

BTL_LINK = 1280  # mega BYTES
THREADS = 12


def calc_jfi(df):
    df = log_plotter.trim_flow_times(log_plotter.TIME_S_TRIM, log_plotter.TIME_S_TRIM, df)
    bws = log_plotter.get_avg_gprs(df, False)
    return metric_calc.get_jfi(bws)


def main():
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [(15, 4000, 600, 'cubic', 20, 0, 0, trial)
                                                                          for trial in range(1, 51)]
    # (15, 800, 600, 'cubic', 20, 0, 0, 50),
    # (10, 6000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 4000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 200, 600, 'cubic', 20, 0, 0, 50),
    # (2, 1500, 600, 'cubic', 20, 0, 0, 50)]

    dfs_demands = log_plotter.get_dfs_and_demands(BTL_LINK,
                                                  nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    pool = mp.Pool(THREADS)
    jfis = pool.map(calc_jfi, list(map(lambda x: x[0], dfs_demands)))

    print("Finished!")

    with open('../results/jfis/%d_nodes_%d_flows_%d_s_%s_algo_rev_%d_nm1_%d_nm2_%d_delayed_%d' % nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l[0], "w") as f:
        f.writelines(map(lambda x: str(x) + '\n', jfis))


if __name__ == '__main__':
    main()
