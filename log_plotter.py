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


def plot_hist(agg_bw_series: pd.DataFrame, cumulative: bool):
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=np.min(agg_bw_series),
                                    size=0.5,
                                    end=np.max(agg_bw_series)),
                         cumulative_enabled=cumulative,
                         marker=dict(color='rgb(25, 25, 100)'))

    layout = go.Layout(
        title="Histogram with Frequency Count"
    )

    fig = go.Figure(data=go.Data([trace]), layout=layout)
    fig.show()


def plot_link_utilization(df: pd.DataFrame, bin_size_s: int):
    df['bin'] = df.apply(lambda row: row['endtime'] // bin_size_s, axis=1)
    bw_series = df.groupby(by="bin").apply(lambda rows: rows['datasize'].sum() / bin_size_s)
    fig = px.line(pd.DataFrame({'Bins': bw_series.index, 'Bandwidth': bw_series.values}),
                  x="Bins", y="Bandwidth", title='Link utilization')
    fig.update_xaxes(title_text='Bins (%ds)' % bin_size_s)
    fig.show()


def main():
    df = pd.read_csv('iperf3_log_parsed_merged_10',
                     names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw'])
    df['endtime'] = df['endtime'] - df['endtime'].min() + 1

    df_partial = df[df['ip'] == '192.168.1.1']
    plot_line_graph(df_partial)
    df_partial = df[df['ip'] == '192.168.1.2']
    plot_line_graph(df_partial)
    df_partial = df[df['ip'] == '192.168.1.3']
    plot_line_graph(df_partial)
    df_partial = df[df['ip'] == '192.168.1.4']
    plot_line_graph(df_partial)
    df_partial = df[df['ip'] == '192.168.1.5']
    plot_line_graph(df_partial)

    plot_link_utilization(df, 60)

    df = trim_flow_times(60, 60, df)
    plot_hist(get_avg_bw(df), False)
    plot_hist(get_avg_bw(df), True)
    pass


main()
