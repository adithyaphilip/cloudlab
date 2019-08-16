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


def plot_cdf(agg_bw_series: pd.DataFrame):
    trace = go.Histogram(x=agg_bw_series,
                         xbins=dict(start=np.min(agg_bw_series),
                                    size=0.25,
                                    end=np.max(agg_bw_series)),
                         marker=dict(color='rgb(25, 25, 100)'))

    layout = go.Layout(
        title="Histogram with Frequency Count"
    )

    fig = go.Figure(data=go.Data([trace]), layout=layout)
    fig.show()


def main():
    df = pd.read_csv('merged_1.txt',
                     names=['ip', 'socket', 'endtime', 'datasize', 'interval', 'bw'])
    df = trim_flow_times(10, 10, df)
    df['endtime'] = df['endtime'] - df['endtime'].min() + 1
    # plot_line_graph(df)
    plot_cdf(get_avg_bw(df))
    pass


main()
