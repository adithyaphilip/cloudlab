import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


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


def plot_line_graph(df: pd.DataFrame):
    # fig = px.line(df, x='endtime', y='bw')
    # fig.show()
    fig = go.Figure()

    for name, group in df.groupby(by=['ip', 'socket']):
        fig.add_trace(go.Scatter(x=group["endtime"], y=group['bw'], name=':'.join(map(str, name))))

    fig.update_layout(title_text='Flow bandwidth over time')
    fig.show()


def plot_hist(agg_bw_series: pd.DataFrame, cumulative: bool, demand_per_flow_mB: float):
    agg_bw_series = agg_bw_series / demand_per_flow_mB
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=np.min(agg_bw_series),
                                    size=0.05,
                                    end=np.max(agg_bw_series)),
                         cumulative_enabled=cumulative,
                         histnorm='percent',
                         marker=dict(color='rgb(25, 25, 100)'))

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


def get_hist(agg_bw_series: pd.DataFrame, cumulative: bool):
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=np.min(agg_bw_series),
                                    size=0.05,
                                    end=np.max(agg_bw_series)),
                         cumulative_enabled=cumulative,
                         marker=dict(color='rgb(25, 25, 100)'))

    return trace


def main():
    btl_link_cap_mB = 1250
    num_flows_per_node = 50
    num_nodes = 5
    demand = btl_link_cap_mB / num_flows_per_node / num_nodes

    df = pd.read_csv('logs/%d_flows_600_s_cubic_algo' % num_flows_per_node,
                     names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw'])
    df['endtime'] = df['endtime'] - df['endtime'].min() + 1

    # df_partial = df[df['ip'] == '192.168.1.1']
    # plot_line_graph(df_partial)
    # df_partial = df[df['ip'] == '192.168.1.2']
    # plot_line_graph(df_partial)
    # df_partial = df[df['ip'] == '192.168.1.3']
    # plot_line_graph(df_partial)
    # df_partial = df[df['ip'] == '192.168.1.4']
    # plot_line_graph(df_partial)
    # df_partial = df[df['ip'] == '192.168.1.5']
    # plot_line_graph(df_partial)

    plot_line_graph(df)

    plot_link_utilization(df, 60, btl_link_cap_mB)

    df = trim_flow_times(60, 60, df)
    plot_hist(get_avg_bw(df), False, demand)
    plot_hist(get_avg_bw(df), True, demand)
    pass


main()
