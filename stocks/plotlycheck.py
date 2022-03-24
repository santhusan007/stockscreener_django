from plotly.offline import plot
import plotly.graph_objs as go

fig = go.Figure()
scatter = go.Scatter(x=[0, 1, 2, 3], y=[0, 1, 2, 3],
                     mode='lines', name='test',
                     opacity=0.8, marker_color='green')
fig.add_trace(scatter)
plt_div = plot(fig, output_type='div')
