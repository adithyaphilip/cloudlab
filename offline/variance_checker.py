import offline.metric_calc as metric_calc
import offline.log_plotter as log_plotter
import os
import sys
import multiprocessing as mp

BTL_LINK = 1280  # mega BYTES


def calc_jfi(df, )

def main():
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [(2, 6000, 600, 'cubic', 20, 0, 0, trial)
                                                                          for trial in range(1, 50)]
    # (15, 800, 600, 'cubic', 20, 0, 0, 50),
    # (10, 6000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 4000, 600, 'cubic', 20, 0, 0, 50),
    # (15, 200, 600, 'cubic', 20, 0, 0, 50),
    # (2, 1500, 600, 'cubic', 20, 0, 0, 50)]

    dfs_demands = log_plotter.get_dfs_and_demands(BTL_LINK,
                                                  nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    jfis = mp.Array('d', len(dfs_demands))
    for df, _ in dfs_demands:
        df = log_plotter.trim_flow_times(log_plotter.TIME_S_TRIM, log_plotter.TIME_S_TRIM, df)
        bws = log_plotter.get_avg_gprs(df, False)
        jfi = metric_calc.get_jfi(bws)
        jfis.append(jfi)

    print("Finished!")

    with open("jfis.out", "w") as f:
        f.writelines(map(lambda x: str(x) + '\n', jfis))


if __name__ == '__main__':
    main()
