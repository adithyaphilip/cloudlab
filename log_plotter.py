from typing import List, Tuple

import pandas as pd
import plotly.subplots as plsb
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math


def trim_flow_times(start_offset_s, end_offset_s, df: pd.DataFrame):
    ip_min_max = df.groupby(by='ip').agg(max_time=('endtime', 'max'), min_time=('endtime', 'min'))
    df_filtered = df[df.apply(
        lambda row: ip_min_max.loc[row['ip']]['min_time'] + start_offset_s
                    <= row['endtime'] <=
                    ip_min_max.loc[row['ip']]['max_time'] - end_offset_s,
        axis=1
    )]
    return df_filtered


def get_avg_bw(df: pd.DataFrame):
    return df.groupby(by=["ip", "socket"]).apply(lambda rows: rows['datasize'].sum() / rows['interval'].sum())


def plot_line_graph(df: pd.DataFrame, demand: float):
    fig = go.Figure()

    for name, group in df.groupby(by=['ip', 'socket']):
        fig.add_trace(go.Scatter(x=group["endtime"], y=group['datasize'] / group['interval'] / demand,
                                 name=':'.join(map(str, name))))

    fig.update_layout(title_text='Flow bandwidth over time')
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


def plot_link_utilization(df: pd.DataFrame, bin_size_s: int, tot_bw_mB: float):
    df['bin'] = df.apply(lambda row: row['endtime'] // bin_size_s, axis=1)
    bw_series = df.groupby(by="bin").apply(lambda rows: rows['datasize'].sum() / bin_size_s / tot_bw_mB)
    fig = px.line(pd.DataFrame({'Bins': bw_series.index, 'Bandwidth': bw_series.values}),
                  x="Bins", y="Bandwidth", title='Link utilization')
    fig.update_xaxes(title_text='Bins (%ds)' % bin_size_s)
    fig.show()


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
                           cols_num=3):

    fig = plsb.make_subplots(rows=math.ceil(len(dfs_demands) / cols_num), cols=cols_num,
                             subplot_titles=["%d Flows" % x for x in flow_counts_ordered])

    ctr = 0
    for df, demand in dfs_demands:
        df_trimmed = trim_flow_times(60, 60, df)
        avg_bws = get_avg_bw(df_trimmed)
        trace = get_hist(avg_bws, cumulative, demand)

        row, col = ctr // cols_num + 1, ctr % cols_num + 1
        fig.add_trace(trace, row=row, col=col)
        fig.update_xaxes(title_text="Goodput/Demand", row=row, col=col, range=[0.5, 2])
        fig.update_yaxes(title_text="% flows", row=row, col=col, range=[0, 100])
        ctr += 1

    fig.update_layout(title_text="Comparing demand satisfaction ratio")
    fig.show()


def plot_multiple_bw_util(flow_counts_ordered: List[int],
                           dfs_demands: List[Tuple[pd.DataFrame, float]],
                           cumulative: bool,
                           cols_num=3):
    pass


def get_dfs_and_demands(blt_link_cap_mb: float, flows_per_node_time_algo_l: List[Tuple[int, int, str]], num_nodes: int):
    dfs_demands = []

    for tup in flows_per_node_time_algo_l:
        df = pd.read_csv('logs/%d_flows_%d_s_%s_algo_3' % tup,
                         names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw'])
        df['endtime'] = df['endtime'] - df['endtime'].min() + 1
        dfs_demands.append((df, blt_link_cap_mb / num_nodes / tup[0]))

    return dfs_demands


def main():
    btl_link_cap_mb = 1250  # mega BYTES
    num_nodes = 5
    flows_per_node_time_algo_l = [(1000, 600, 'cubic')]
    # flows_per_node_time_algo_l = [(400, 600, 'cubic'), (200, 600, 'cubic'), (100, 600, 'cubic'),
    #                               (50, 600, 'cubic'), (10, 600, 'cubic'), (1, 600, 'cubic')]
    # flows_per_node_time_algo_l = [(1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic'), (1, 600, 'cubic')]

    dfs_demands = get_dfs_and_demands(btl_link_cap_mb, flows_per_node_time_algo_l, num_nodes)

    for df, demand in dfs_demands:
        plot_line_graph(df, demand)

        plot_link_utilization(df, 60, btl_link_cap_mb)

        df = trim_flow_times(60, 60, df)
        plot_hist(get_avg_bw(df), False, demand)
        plot_hist(get_avg_bw(df), True, demand)

    # plot_multiple_exp_hist([x[0] * num_nodes for x in flows_per_node_time_algo_l], dfs_demands, False)


main()
