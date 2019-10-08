from typing import List, Tuple, Dict

import pandas as pd
import plotly.subplots as plsb
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import itertools

import offline.metric_calc as metric_calc


# TODO: This trims the first and last X seconds from the start and end of _each_ flow. We ideally want it to remove
# logs from the start and end of any of the flows
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
    return df_grp.apply(lambda rows: rows['datasize'].sum() / (rows['endtime'].max() - rows['endtime'].min()))


def get_tot_avg_gpr(df: pd.DataFrame):
    return df['datasize'].sum() / (df['endtime'].max() - df['endtime'].min())


def plot_line_graph(df: pd.DataFrame, demand: float, selective: bool, flow_count, trim=False, top=10, mid=10, bot=10):
    fig = go.Figure()

    if trim:
        df = trim_flow_times(60, 60, df)

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
    df['bin'] = df.apply(lambda row: row['endtime'] // bin_size_s, axis=1)
    bw_series = df.groupby(by="bin").apply(lambda rows: rows['datasize'].sum() / bin_size_s / tot_bw_mb)
    return go.Scatter(x=bw_series.index, y=bw_series.values, mode='lines+markers', name=name)


def get_hist(agg_bw_series: pd.DataFrame, cumulative: bool, demand_per_flow_mb: float):
    agg_bw_series = agg_bw_series / demand_per_flow_mb
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=0,
                                    size=0.05,
                                    end=2),
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
        df_trimmed = trim_flow_times(60, 60, df)
        avg_bws = get_avg_gprs(df_trimmed, False)
        trace = get_hist(avg_bws, cumulative, demand)
        avg_gpr_ratio = get_tot_avg_gpr(df) / btl_bw_mb
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
        trace = get_link_util(df, bin_size_s, btl_bw_mb, name='%d Flows' % flow_counts_ordered[ctr])

        row, col = ctr // cols_num + 1, ctr % cols_num + 1
        fig.add_trace(trace, row=row, col=col)
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="%Goodput Rate/Bottleneck Bandwidth", row=row, col=col, range=[0.3, 1.1])
        ctr += 1

    fig.update_layout(title_text="Comparing demand satisfaction ratio")
    fig.show()


def plot_jfis(keys_to_flows_to_df: Dict[str, Dict[int, pd.DataFrame]]):
    fig = go.Figure()
    fig.update_xaxes(title_text='flow count')
    fig.update_yaxes(title_text='JFI', range=[0, 1])
    fig.update_layout(title_text='JFI vs flow count')

    for key, flows_to_df in keys_to_flows_to_df.items():
        dfs_trimmed_sorted = [trim_flow_times(60, 60, df) for _, df in sorted(flows_to_df.items(), key=lambda x: x[0])]
        # JFI where every flow is an individual entity
        ordered_jfis = [metric_calc.get_jfi(get_avg_gprs(df, False)) for df in dfs_trimmed_sorted]

        # JFI where every host is a single entity (we group the flows under each host)
        ordered_jfis_hosts = [metric_calc.get_jfi(get_avg_gprs(df, True)) for df in dfs_trimmed_sorted]

        fig.add_trace(go.Scatter(x=sorted(flows_to_df), y=ordered_jfis, name=key))
        fig.add_trace(go.Scatter(x=sorted(flows_to_df), y=ordered_jfis_hosts, name=key + "_hosts"))

    fig.show()


def get_dfs_and_demands(blt_link_cap_mb: float, nodes_flows_per_node_time_algo_l: List[Tuple[int, int, int, str]]):
    dfs_demands = []

    for tup in nodes_flows_per_node_time_algo_l:
        df = pd.read_csv('../logs/%d_nodes_%d_flows_%d_s_%s_algo' % tup,
                         names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw', 'retries'])
        df['endtime'] = df['endtime'] - df['endtime'].min() + 1
        dfs_demands.append((df, blt_link_cap_mb / tup[0] / tup[1]))

    return dfs_demands


def get_df_custom(filepath: str, demand: float):
    df = pd.read_csv(filepath,
                     names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw', 'retries'])
    df['endtime'] = df['endtime'] - df['endtime'].min() + 1

    return (df, demand)


def main():
    btl_link_cap_mb = 1280  # mega BYTES
    nodes_flows_per_node_time_algo_l = [(5, 6000, 600, 'reno'), (10, 3000, 600, 'reno'), (15, 2000, 600, 'reno'),
                                        (5, 3000, 600, 'reno'), (10, 1500, 600, 'reno'), (15, 1000, 600, 'reno'),
                                        (5, 300, 600, 'reno'), (10, 150, 600, 'reno'), (15, 100, 600, 'reno')]
    # nodes_flows_per_node_time_algo_l = [(5, 200, 600, 'reno'), (5, 400, 600, 'reno'), (5, 1000, 600, 'reno'),
    #                               (5, 2000, 600, 'reno'), (5, 4000, 600, 'reno'), (5, 8000, 600, 'reno')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (10, 600, 'cubic'), (50, 600, 'cubic'), (100, 600, 'cubic'),
    #                               (200, 600, 'cubic'), (400, 600, 'cubic'), (1000, 600, 'cubic'),
    #                               (2000, 600, 'cubic'), (4000, 600, 'cubic'), (8000, 600, 'cubic')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (10, 600, 'cubic'), (50, 600, 'cubic'), (100, 600, 'cubic')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic')]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb, nodes_flows_per_node_time_algo_l)

    # for df_demand, flows_per_node in zip(dfs_demands, map(lambda x: x[0], flows_per_node_time_algo_l)):
    #     df, demand = df_demand
    #     plot_line_graph(df, demand, True, flow_count=num_nodes * flows_per_node, trim=True, top=2, bot=2, mid=2)

    #   plot_link_utilization(df, 60, btl_link_cap_mb)

    #   plot_hist(get_avg_gprs(df), False, demand)
    #   plot_hist(get_avg_gprs(df), True, demand)

    plot_jfis(
        {str(nodes): {int(btl_link_cap_mb / demand): df for df, demand in map(lambda x: x[1], grp)}
         for nodes, grp
         in itertools.groupby(sorted(zip(nodes_flows_per_node_time_algo_l, dfs_demands), key=lambda x:x[0][0]), key=lambda x: x[0][0])
         })
    plot_multiple_exp_hist([x[1] * x[0] for x in nodes_flows_per_node_time_algo_l], dfs_demands, False, btl_link_cap_mb,
                           cols_num=2)
    plot_multiple_exp_hist([x[1] * x[0] for x in nodes_flows_per_node_time_algo_l], dfs_demands, True, btl_link_cap_mb,
                           cols_num=2)
    plot_multiple_bw_util([x[1] * x[0] for x in nodes_flows_per_node_time_algo_l], dfs_demands, btl_link_cap_mb,
                          cols_num=2)


main()
