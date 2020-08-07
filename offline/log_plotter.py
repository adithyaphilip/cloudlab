from typing import List, Tuple, Dict

import pandas as pd
import plotly.subplots as plsb
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import itertools
import consts
import os
import sys
import offline.metric_calc as metric_calc

TIME_S_TRIM_END = 30
TIME_S_TRIM_START = 120
IND_TYPE2_COUNT = 6
IND_BASE_RTT = 4
IND_FLOWS_PER_NODE = 1
IND_NUM_NODES = 0


# TODO: This trims the first and last X seconds from the start and end of _each_ flow. We ideally want it to remove
# logs from the start and end of any of the flows. NOTE: Doesn't this function already do this?
def trim_flow_times(start_offset_s, end_offset_s, df: pd.DataFrame):
    min_time = df['endtime'].min()
    max_time = df['endtime'].max()
    df_filtered = df[df.apply(
        lambda row: min_time + start_offset_s <= row['endtime'] <= max_time - end_offset_s,
        axis=1
    )]
    return df_filtered


# gprs - goodput rates
def get_avg_gprs(df: pd.DataFrame, host_level: bool):
    df_grp = df.groupby(by=["ip"]) if host_level else df.groupby(by=["ip", "socket"])
    result = df_grp.apply(
        lambda rows: rows['datasize'].sum() / (
                rows['endtime'].max() - rows['endtime'].min())) if host_level else df_grp.apply(
        lambda rows: rows['datasize'].sum() / rows['interval'].sum())

    print("LOG: GET_AVG_GPRS - detected %d distinct rows with host_level %s" % (len(result), str(host_level)))

    return result


def get_tot_avg_gpr(df: pd.DataFrame):
    tot_data = df['datasize'].sum()
    tot_time = df['endtime'].max() - df['endtime'].min()
    return tot_data / tot_time


def plot_line_graph(df: pd.DataFrame, demand: float, selective: bool, flow_count, trim=False, top=10, mid=10, bot=10):
    fig = go.Figure()

    if trim:
        df = trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df)

    df_grp = df.groupby(by=['ip', 'socket'])

    if selective and top + mid + bot < len(df_grp):  # we are selecting less than the number of avail rows
        vals = list(sorted(df_grp['datasize'].sum()))
        top_lim_min = vals[-top]
        bot_lim_max = vals[bot]
        mid_lim_max = vals[len(vals) // 2 + mid // 2 - 1]
        mid_lim_min = vals[len(vals) // 2 - mid // 2]

        df_bot = df_grp.filter(lambda subdf: subdf['datasize'].sum() <= bot_lim_max).groupby(by=['ip', 'socket'])
        df_top = df_grp.filter(lambda subdf: subdf['datasize'].sum() >= top_lim_min).groupby(by=['ip', 'socket'])
        df_mid = df_grp.filter(lambda subdf: mid_lim_min <= subdf['datasize'].sum() <= mid_lim_max).groupby(
            by=['ip', 'socket'])
        color_grps = [(df_bot, 'violet'), (df_mid, 'green'), (df_top, 'red')]

        for raw_grp, color in color_grps:
            for name, group in raw_grp:
                fig.add_trace(go.Scatter(x=group["endtime"], y=group['datasize'] / group['interval'] / demand,
                                         name=':'.join(map(str, name)), line={'color': color}))

    else:
        for name, group in df_grp:
            fig.add_trace(go.Scatter(x=group["endtime"], y=group['datasize'] / group['interval'] / demand,
                                     name=':'.join(map(str, name))))

    fig.update_layout(title_text='Flow bandwidth over time - %d flows' % flow_count)
    fig.show()


def plot_hist(agg_bw_series: pd.DataFrame, cumulative: bool, demand_per_flow_mb: float):
    trace = get_hist(agg_bw_series, cumulative, demand_per_flow_mb)

    layout = go.Layout(
        title="Histogram with %"
    )

    fig = go.Figure(data=go.Data([trace]), layout=layout)
    fig.update_xaxes(range=[0, 2])
    fig.update_yaxes(range=[0, 100])
    fig.show()


def plot_link_utilization(df: pd.DataFrame, bin_size_s: int, tot_bw_mb: float):
    df['bin'] = df.apply(lambda row: row['endtime'] // bin_size_s, axis=1)
    bw_series = df.groupby(by="bin").apply(lambda rows: rows['datasize'].sum() / bin_size_s / tot_bw_mb)
    fig = px.line(pd.DataFrame({'Bins': bw_series.index, 'Bandwidth': bw_series.values}),
                  x="Bins", y="Bandwidth", title='Link utilization')
    fig.update_xaxes(title_text='Bins (%ds)' % bin_size_s)
    fig.show()


def get_link_util(df: pd.DataFrame, bin_size_s: int, tot_bw_mb: float, name: str):
    df = df.assign(bin=df.apply(lambda row: row['endtime'] // bin_size_s, axis=1))
    bw_series = df.groupby(by="bin").apply(lambda rows: rows['datasize'].sum() / bin_size_s / tot_bw_mb)
    return go.Scatter(x=bw_series.index, y=bw_series.values, mode='lines+markers', name=name)


def get_hist(agg_bw_series: pd.DataFrame, cumulative: bool, demand_per_flow_mb: float):
    agg_bw_series = agg_bw_series / demand_per_flow_mb
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=0,
                                    size=0.05,
                                    end=max(2, agg_bw_series.max())),
                         cumulative_enabled=cumulative,
                         histnorm='percent',
                         marker=dict(color='rgb(25, 25, 100)'))
    return trace


def plot_multiple_exp_hist(flow_counts_ordered: List[int],
                           dfs_demands: List[Tuple[pd.DataFrame, float]],
                           cumulative: bool,
                           btl_bw_mb: float,
                           cols_num=3):
    fig = plsb.make_subplots(rows=math.ceil(len(dfs_demands) / cols_num), cols=cols_num,
                             subplot_titles=["%d Flows" % x for x in flow_counts_ordered])

    ctr = 0
    for df, demand in dfs_demands:
        df_trimmed = trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df)
        avg_bws = get_avg_gprs(df_trimmed, False)
        trace = get_hist(avg_bws, cumulative, demand)
        avg_gpr_ratio = get_tot_avg_gpr(df_trimmed) / btl_bw_mb
        trace2 = go.Scatter(x=[avg_gpr_ratio, avg_gpr_ratio], y=[0, 100], name='Overall Goodput Rate', mode='lines')

        row, col = ctr // cols_num + 1, ctr % cols_num + 1
        fig.add_trace(trace, row=row, col=col)
        fig.add_trace(trace2, row=row, col=col)
        fig.update_xaxes(title_text="Goodput Rate/Demand", row=row, col=col, range=[0, 2])
        fig.update_yaxes(title_text="% flows", row=row, col=col, range=[0, 100])
        ctr += 1

    fig.update_layout(title_text="Comparing demand satisfaction ratio")
    fig.show()


def plot_multiple_bw_util(flow_counts_ordered: List[int],
                          dfs_demands: List[Tuple[pd.DataFrame, float]],
                          btl_bw_mb: float,
                          bin_size_s: int = 60,
                          cols_num: int = 3):
    fig = plsb.make_subplots(rows=math.ceil(len(dfs_demands) / cols_num), cols=cols_num,
                             subplot_titles=["%d Flows" % x for x in flow_counts_ordered])

    ctr = 0
    for df, demand in dfs_demands:
        trace = get_link_util(trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df), bin_size_s, btl_bw_mb,
                              name='%d Flows' % flow_counts_ordered[ctr])

        row, col = ctr // cols_num + 1, ctr % cols_num + 1
        fig.add_trace(trace, row=row, col=col)
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="%Goodput Rate/Bottleneck Bandwidth", row=row, col=col, range=[0.3, 1.1])
        ctr += 1

    fig.update_layout(title_text="Comparing demand satisfaction ratio")
    fig.show()


def plot_avg_bw_util(keys_to_flows_to_df: Dict[str, Dict[int, pd.DataFrame]],
                     btl_bw_mb: float):
    fig = go.Figure()
    fig.update_xaxes(title_text='Flow Count')
    fig.update_yaxes(title_text='Goodput Fraction', range=[0, 1])
    fig.update_layout(title_text='Goodput Fraction vs Flow Count')

    for key, flows_to_df in keys_to_flows_to_df.items():
        dfs_trimmed_sorted = [trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df) for _, df in
                              sorted(flows_to_df.items(), key=lambda x: x[0])]
        ordered_gprs = [get_tot_avg_gpr(df) / btl_bw_mb for df in dfs_trimmed_sorted]

        fig.add_trace(go.Scatter(x=sorted(flows_to_df), y=ordered_gprs, name=key))

    fig.show()


def plot_jfis(keys_to_flows_to_df: Dict[str, Dict[int, pd.DataFrame]]):
    fig = go.Figure()
    fig.update_xaxes(title_text='flow count')
    fig.update_yaxes(title_text='JFI', range=[0, 1])
    fig.update_layout(title_text='JFI vs flow count')

    for key, flows_to_df in keys_to_flows_to_df.items():
        dfs_trimmed_sorted = [trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df) for _, df in
                              sorted(flows_to_df.items(), key=lambda x: x[0])]
        # JFI where every flow is an individual entity
        ordered_jfis = [metric_calc.get_jfi(get_avg_gprs(df, False)) for df in dfs_trimmed_sorted]

        # JFI where every host is a single entity (we group the flows under each host)
        ordered_jfis_hosts = [metric_calc.get_jfi(get_avg_gprs(df, True)) for df in dfs_trimmed_sorted]

        fig.add_trace(go.Scatter(x=sorted(flows_to_df), y=ordered_jfis, name=key))
        fig.add_trace(go.Scatter(x=sorted(flows_to_df), y=ordered_jfis_hosts, name=key + "_hosts"))

    fig.show()


# just accepts a list of dataframes, where each dataframe contains logging information for all flows.
# meant to be used just to plot JFIs for same number of flows for multiple trials. This func does not try to interpret
# number of flows etc.
def plot_jfis_trials(dfs_l: List[pd.DataFrame], title: str):
    fig = go.Figure()
    fig.update_xaxes(title_text='trial')
    fig.update_yaxes(title_text='JFI', range=[0, 1])
    fig.update_layout(title_text='JFI vs trial: %s' % title)

    dfs_l = [trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, df) for df in dfs_l]
    # JFI where every flow is an individual entity
    jfis_flow_level = [metric_calc.get_jfi(get_avg_gprs(df, False)) for df in dfs_l]
    # JFI where every host is a single entity (we group the flows under each host)
    jfis_host_level = [metric_calc.get_jfi(get_avg_gprs(df, True)) for df in dfs_l]

    fig.add_trace(go.Scatter(x=sorted(range(1, 1 + len(dfs_l))), y=jfis_flow_level, name="flow level"))
    fig.add_trace(go.Scatter(x=sorted(range(1, 1 + len(dfs_l))), y=jfis_host_level, name="host level"))

    fig.show()


def get_dfs_and_demands(blt_link_cap_mb: float,
                        nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l: List[
                            Tuple[int, int, int, str, int, int, int, int]]):
    dfs_demands = []

    for tup in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l:
        filepath = '../logs/%d_nodes_%d_flows_%d_s_%s_algo_rev_%d_nm1_%d_nm2_%d_delayed_%d' % tup
        if not os.path.exists(filepath):
            print("ERROR: Could not find logfile %s, ABORT if unexpected!" % filepath, file=sys.stderr)
            continue
        df = pd.read_csv(filepath,
                         names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw', 'retries'])
        df['endtime'] = df['endtime'] - df['endtime'].min() + 20
        dfs_demands.append((df, blt_link_cap_mb / tup[0] / tup[1]))

    return dfs_demands


def get_df_custom(filepath: str, demand: float):
    df = pd.read_csv(filepath,
                     names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw', 'retries'])
    df['endtime'] = df['endtime'] - df['endtime'].min() + 1

    return (df, demand)


# Builds a dict that maps from key_index_list[0] -> key_index_list[1] -> key_index_list[2] until we get to the DF
# index here refers to position of the key in the id_tup
def get_dict_from_id_tups_dfs(key_index_list: List[int], id_tups_dfs: List):
    key_index = key_index_list[0]
    keys = np.unique(np.array(list(map(lambda x: x[0][key_index], id_tups_dfs))))

    dict_here = {key: [id_tup_df for id_tup_df in id_tups_dfs if id_tup_df[0][key_index] == key] for key in keys}

    if len(key_index_list) == 1:
        return dict_here
    else:
        return {key: get_dict_from_id_tups_dfs(key_index_list[1:], val) for key, val in dict_here.items()}


def split_df_by_rtt(df: pd.DataFrame, type2_count: int):
    type2_ips = {consts.IP_PREFIX + str(i) for i in range(1, 1 + type2_count)}
    mask = df["ip"].isin(list(type2_ips))
    df_2 = df[mask]
    df_1 = df[~mask]

    return df_1, df_2


def get_bw_by_rtt(df_trimmed: pd.DataFrame, type2_count: int, tot_count: int, fraction: bool):
    df_1, df_2 = split_df_by_rtt(df_trimmed, type2_count)

    avg_type2 = get_tot_avg_gpr(df_2) / type2_count
    avg_type1 = get_tot_avg_gpr(df_1) / (tot_count - type2_count)

    type2_frac = avg_type2 / (avg_type1 + avg_type2)
    type1_frac = 1 - type2_frac

    return type1_frac if fraction else avg_type1, type2_frac if fraction else avg_type2


# Plots b/w per node for low RTT and high RTT nodes, and shows fraction of total goodput taken by each
# id_tup_df: Tuple of the id tuple and the df
# ASSUMPTION: Only 1 type2 RTT is being displayed, just variants of number of nodes with that RTT and number of flows
def rtt_plot_bw_per_node(id_tup_dfs_trimmed: List, tot_nodes: int, fraction: bool):
    type2_counts_to_id_tup_dfs = get_dict_from_id_tups_dfs([IND_TYPE2_COUNT], id_tup_dfs_trimmed)
    fig = go.Figure()
    fig.update_xaxes(title_text='Flow count')
    fig.update_yaxes(title_text='Normalized Goodput Fraction', range=[0, 1])
    fig.update_layout(title_text='Flow Count vs Normalized Goodput Fraction')

    for type2_count, id_tup_dfs in type2_counts_to_id_tup_dfs.items():
        bw_fracs_ordered_by_flows = [get_bw_by_rtt(id_tup_df[1], type2_count, tot_nodes, fraction)
                                     for id_tup_df in sorted(id_tup_dfs, key=lambda x: x[0][IND_FLOWS_PER_NODE])]
        type1_ordered_by_flows = list(map(lambda x: x[0], bw_fracs_ordered_by_flows))
        type2_ordered_by_flows = list(map(lambda x: x[1], bw_fracs_ordered_by_flows))

        fig.add_trace(go.Scatter(
            x=sorted(map(lambda x: x[0][IND_FLOWS_PER_NODE] * x[0][IND_NUM_NODES], id_tup_dfs)),
            y=type1_ordered_by_flows,
            name="type1 - (%d type2)" % type2_count))
        fig.add_trace(go.Scatter(
            x=sorted(map(lambda x: x[0][IND_FLOWS_PER_NODE] * x[0][IND_NUM_NODES], id_tup_dfs)),
            y=type2_ordered_by_flows,
            name="type2 - (%d type2)" % type2_count))

    fig.show()


# this one computes the ratio of throughput on the y-axis for different RTT ratios on the x-axis,
# for a given type2 count. Shows avg type2 rtt bw / avg type1 rtt bw vs base rtt / type2 rtt
def gen_graphs_rtt_comp_throughput(base_rtts_ms: List[int], type2_rtt_ms: int, used_nodes: int, tot_flows: int,
                                   duration_s: int,
                                   type2_count: int,
                                   cca: str, btl_link_cap_mb: float):
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
        (used_nodes, tot_flows // used_nodes, duration_s, cca, base_rtt_ms, type2_rtt_ms, type2_count, 1)
        for base_rtt_ms in base_rtts_ms]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
                                      nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)
    res = []
    for id_tup, df_demand in zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l, dfs_demands):
        avg_type1, avg_type2 = get_bw_by_rtt(
            df_trimmed=trim_flow_times(TIME_S_TRIM_START, TIME_S_TRIM_END, df_demand[0]),
            fraction=False,
            tot_count=used_nodes,
            type2_count=type2_count
        )
        res.append((avg_type2 / avg_type1, id_tup[IND_BASE_RTT] / type2_rtt_ms))

    x = []
    y = []
    for bw_ratio, rtt_ratio in sorted(res, key=lambda p: p[1]):
        x.append(rtt_ratio)
        y.append(bw_ratio)

    fig = go.Figure(data=go.Scatter(x=x, y=y))
    fig.show()


def gen_graphs_rtt_comp2(base_rtts_ms: List[int], type2_rtt_ms: int, nodes: int, flow_list: List[int],
                         duration_s: int,
                         type2_counts: List[int],
                         cca: str,
                         btl_link_cap_mb: int):
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
        (nodes, tot_flows // nodes, duration_s, cca, base_rtt_ms, type2_rtt_ms, type2_count, 1)
        for base_rtt_ms in base_rtts_ms
        for tot_flows in flow_list
        for type2_count in type2_counts]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
                                      nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    if len(type2_counts) == 1:
        plot_multiple_exp_hist([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
                                for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
                               dfs_demands, False,
                               btl_link_cap_mb,
                               cols_num=3)
        plot_multiple_exp_hist([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
                                for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
                               dfs_demands, True,
                               btl_link_cap_mb,
                               cols_num=3)
        # plot_multiple_bw_util([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
        #                        for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
        #                       dfs_demands, btl_link_cap_mb,
        #                       cols_num=2)

    else:
        plot_jfis(
            {str(type2_count_base_rtt): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
             for type2_count_base_rtt, grp
             in itertools.groupby(
                sorted(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l, dfs_demands),
                       key=lambda x: (x[0][IND_TYPE2_COUNT], x[0][IND_BASE_RTT])),
                key=lambda x: (x[0][IND_TYPE2_COUNT], x[0][IND_BASE_RTT]))
             })

        id_tups_dfs_trimmed = list(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l,
                                       map(lambda x: trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, x[0]),
                                           dfs_demands)
                                       ))
        # id_tups_dfs = list(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l,
        #                        map(lambda x: x[0], dfs_demands)
        #                        ))
        rtt_plot_bw_per_node(id_tups_dfs_trimmed, nodes, True)
        rtt_plot_bw_per_node(id_tups_dfs_trimmed, nodes, False)


def gen_graphs_rtt_comp(base_rtt_ms: int, type2_rtt_ms: int, nodes: int, flow_list: List[int], type2_counts: List[int],
                        cca: str,
                        btl_link_cap_mb: int):
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
        (nodes, tot_flows // nodes, 600, cca, base_rtt_ms, type2_rtt_ms, type2_count, 1)
        for tot_flows in flow_list
        for type2_count in type2_counts]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
                                      nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    if len(type2_counts) == 1:
        plot_multiple_exp_hist([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
                                for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
                               dfs_demands, False,
                               btl_link_cap_mb,
                               cols_num=3)
        plot_multiple_exp_hist([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
                                for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
                               dfs_demands, True,
                               btl_link_cap_mb,
                               cols_num=3)
        # plot_multiple_bw_util([x[IND_FLOWS_PER_NODE] * x[IND_NUM_NODES]
        #                        for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
        #                       dfs_demands, btl_link_cap_mb,
        #                       cols_num=2)

    else:
        plot_jfis(
            {str(type2_count): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
             for type2_count, grp
             in itertools.groupby(
                sorted(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l, dfs_demands),
                       key=lambda x: x[0][IND_TYPE2_COUNT]),
                key=lambda x: x[0][IND_TYPE2_COUNT])
             })

        id_tups_dfs_trimmed = list(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l,
                                       map(lambda x: trim_flow_times(TIME_S_TRIM_END, TIME_S_TRIM_END, x[0]),
                                           dfs_demands)
                                       ))
        # id_tups_dfs = list(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l,
        #                        map(lambda x: x[0], dfs_demands)
        #                        ))
        rtt_plot_bw_per_node(id_tups_dfs_trimmed, nodes, True)
        rtt_plot_bw_per_node(id_tups_dfs_trimmed, nodes, False)


# generate graphs for when we vary base delay
def gen_graphs_rtt_uniform(base_rtts_ms: List[int], nodes: int, flow_list: List[int], cca: str, btl_link_cap_mb: int):
    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
        (nodes, tot_flows // nodes, 600, cca, rtt, 0, 0, 2)
        for tot_flows in flow_list
        for rtt in base_rtts_ms
    ]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
                                      nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    delay_flows_df = {str(base_rtt): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
                      for base_rtt, grp
                      in itertools.groupby(
            sorted(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l, dfs_demands),
                   key=lambda x: x[0][IND_BASE_RTT]),
            key=lambda x: x[0][IND_BASE_RTT])
                      }

    plot_jfis(delay_flows_df)

    plot_avg_bw_util(delay_flows_df, btl_link_cap_mb)


def main():
    print('Starting!')
    btl_link_cap_mb = 1280  # mega BYTES
    # nodes_flows_per_node_time_algo_l = [(5, 6000, 600, 'reno'), (10, 3000, 600, 'reno'), (15, 2000, 600, 'reno'),
    #                                     (5, 3000, 600, 'reno'), (10, 1500, 600, 'reno'), (15, 1000, 600, 'reno'),
    #                                     (5, 300, 600, 'reno'), (10, 150, 600, 'reno'), (15, 100, 600, 'reno')]
    # nodes_flows_per_node_time_algo_l = [(5, 200, 600, 'reno'), (5, 400, 600, 'reno'), (5, 1000, 600, 'reno'),
    #                               (5, 2000, 600, 'reno'), (5, 4000, 600, 'reno'), (5, 8000, 600, 'reno')]

    nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
        (nodes, tot_flows // nodes, 1800, 'reno', 20, 20, 0, trial)
        for tot_flows in [2, 200, 2000, 4000, 8000, 12000]
        for nodes in [2]
        for trial in range(1, 1 + 1)]

    # dfs_demands = get_dfs_and_demands(btl_link_cap_mb, nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    for df, dem in get_dfs_and_demands(btl_link_cap_mb, [(2, 1, 1800, 'reno', 20, 0, 0, 1)]):
        plot_line_graph(df, dem, False, 2)
    # nodes_flows_per_node_time_algo_trial_l = list(map(lambda x: (*x[0], x[1]), zip([(nodes, tot_flows // nodes, 600, 'reno')
    #                                           for tot_flows in [3000, 12000, 30000]
    #                                           for nodes in [5, 10, 15]], [2, 1, 1, 4, 1, 1, 3, 2, 1])))

    # nodes_flows_per_node_time_algo_l = [(nodes, tot_flows // nodes, 600, 'reno')
    #                                     for tot_flows in [30000]
    #                                     for nodes in [10]]

    # nodes_flows_per_node_time_algo_l = [(1, 6000, 600, 'reno'), (2, 3000, 600, 'reno'),
    #                                     (1, 4000, 600, 'reno'), (2, 2000, 600, 'reno'),
    #                                     (1, 2000, 600, 'reno'), (2, 1000, 600, 'reno'),
    #                                     (1, 1000, 600, 'reno'), (2, 500, 300, 'reno'), (1, 500, 600, 'reno'),
    #                                     (2, 250, 300, 'reno')]
    # nodes_flows_per_node_time_algo_l = [(1, 4000, 600, 'reno')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (10, 600, 'cubic'), (50, 600, 'cubic'), (100, 600, 'cubic')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic')]

    # dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
    #                                   nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)

    # for df_demand, flows_per_node in zip(dfs_demands, map(lambda x: x[0], flows_per_node_time_algo_l)):
    #     df, demand = df_demand
    #     plot_line_graph(df, demand, True, flow_count=num_nodes * flows_per_node, trim=True, top=2, bot=2, mid=2)

    #   plot_link_utilization(df, 60, btl_link_cap_mb)

    #   plot_hist(get_avg_gprs(df), False, demand)
    #   plot_hist(get_avg_gprs(df), True, demand)
    #
    # for tot_flows in [3000, 15000, 30000, 60000]:
    #     for nodes in [15]:
    #         for delay in [500, 200, 100, 50, 20, 10, 5]:
    #             nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l = [
    #                 (nodes, tot_flows // nodes, 600, 'cubic', delay, 0, 0, trial)
    #                 for trial in range(1, 1 + 5)
    #             ]
    #             dfs_demands = get_dfs_and_demands(btl_link_cap_mb,
    #                                               nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l)
    #             # plot_jfis_trials([tup[0] for tup in dfs_demands], "%d flows %d ms RTT" % (tot_flows, delay))
    #
    #             plot_multiple_exp_hist(
    #                 [x[1] * x[0] for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
    #                 dfs_demands, False,
    #                 btl_link_cap_mb,
    #                 cols_num=3)
    #
    # plot_jfis(
    #     {str(nodes): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
    #      for nodes, grp
    #      in itertools.groupby(sorted(zip(nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l, dfs_demands), key=lambda x: x[0][0]),
    #                           key=lambda x: x[0][0])
    #      })

    # plot_multiple_exp_hist([x[1] * x[0] for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
    #                        dfs_demands, False,
    #                        btl_link_cap_mb,
    #                        cols_num=3)
    # plot_multiple_exp_hist([x[1] * x[0] for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
    #                        dfs_demands, True,
    #                        btl_link_cap_mb,
    #                        cols_num=3)
    # plot_multiple_bw_util([x[1] * x[0] for x in nodes_flows_per_node_time_algo_basertt_type2rtt_type2count_trial_l],
    #                       dfs_demands, btl_link_cap_mb,
    #                       cols_num=3)
    #
    # plot_avg_bw_util(
    #     {str(nodes): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
    #      for nodes, grp
    #      in itertools.groupby(sorted(zip(nodes_flows_per_node_time_algo_trial_l, dfs_demands), key=lambda x: x[0][0]),
    #                           key=lambda x: x[0][0])
    #      }, btl_link_cap_mb)

    # plot_link_utilization(dfs_demands[0][0], 60, btl_link_cap_mb)


if __name__ == '__main__':
    main()
    # gen_graphs_rtt_comp_throughput([5, 10, 15, 20, 25], 5, 2, 2, 1200, 1, 'reno', btl_link_cap_mb=1280)
    # gen_graphs_rtt_uniform([5, 10, 20, 50, 100, 200, 500], 15, [3000, 15000, 30000, 60000], "cubic", 1280)
    # gen_graphs_rtt_comp(40, 20, 12, [1200, 12000, 48000, 72000], [3, 6, 9], "reno", 1280)
    # gen_graphs_rtt_comp2([40, 100], 20, 12, [1200, 12000, 48000, 72000], [3, 6, 9], "reno", 1280)
    # gen_graphs_rtt_comp(100, 20, 12, [1200, 12000, 48000, 72000], [3, 6, 9], "reno", 1280)
    # gen_graphs_rtt_comp(200, 20, 12, [1200, 12000, 48000, 72000], [3, 6, 9], "reno", 1280)
# gen_graphs_rtt_comp(20, 200, 15, [3000, 15000, 30000, 60000], [4], "reno", 1280)
# gen_graphs_rtt_comp(20, 200, 15, [3000, 15000, 30000, 60000], [8], "reno", 1280)
# gen_graphs_rtt_comp(20, 200, 15, [3000, 15000, 30000, 60000], [12], "reno", 1280)
# gen_graphs_rtt_comp(20, 200, 15, [3000, 15000, 30000, 60000], [15], "reno", 1280)
# gen_graphs_rtt_comp(20, 200, 15, [3000, 15000, 30000, 60000], [8], "cubic", 1280)

# 0:
# 4: 1 1 1 1(3)
# 8: 1 1 1 1(4)
# 12: 1 1 1 1(4)
# 15: 1 1 1 1 1
