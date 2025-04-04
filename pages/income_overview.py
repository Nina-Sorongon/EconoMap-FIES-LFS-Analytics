import dash
from dash import html, dcc, Input, Output
import pandas as pd
import plotly.graph_objects as go

dash.register_page(__name__, path='/', name='Income Overview')

df = pd.read_csv("Family Income and Expenditure.csv")
income_column = "Total Household Income"
food_expenditure_column = "Total Food Expenditure"

# Binning
income_bins = [0, 50000, 150000, 300000, 500000, 1000000, float("inf")]
income_labels = ["<50K", "50K-150K", "150K-300K", "300K-500K", "500K-1M", "1M+"]

df["Income Range"] = pd.cut(df[income_column], bins=income_bins, labels=income_labels, include_lowest=True)
df["Income Range"] = pd.Categorical(df["Income Range"], categories=income_labels, ordered=True)

# Cool-toned color palette (blue to aqua to light green)
cool_colors = ['#0077b6', '#00a8e8', '#90e0ef', '#48cae4', '#00c49a', '#38b000']

def generate_bar():
    income_counts = df["Income Range"].value_counts(sort=False)
    fig = go.Figure(data=[
        go.Bar(
            x=income_labels,
            y=income_counts.values,
            marker=dict(color=cool_colors)
        )
    ])
    fig.update_layout(
        title="Number of Households by Income Group",
        xaxis_title="Income Range (PHP)",
        yaxis_title="Number of Households",
        template="plotly_dark",
        font=dict(family="Segoe UI, Arial, sans-serif", size=14)
    )
    return fig

def generate_violin(selected=None):
    fig = go.Figure()
    for idx, label in enumerate(income_labels):
        data = df[df["Income Range"] == label][food_expenditure_column]
        if not data.empty:
            color = "#00b4d8" if label == selected else cool_colors[idx]
            fig.add_trace(go.Violin(
                y=data, x=[label]*len(data),
                box_visible=True, meanline_visible=True,
                line_color=color, fillcolor=color,
                opacity=0.75 if label != selected else 0.95,
                name=label, showlegend=False
            ))
    fig.update_layout(
        title="Food Expenditure Distribution by Income Group",
        yaxis_title="Total Food Expenditure (PHP)",
        template="plotly_dark",
        font=dict(family="Segoe UI", size=14)
    )
    return fig

layout = html.Div([
    dcc.Graph(id='bar-chart', figure=generate_bar(), style={'marginBottom': '40px'}),
    dcc.Graph(id='violin-chart', figure=generate_violin())
], style={'padding': '20px'})

@dash.callback(
    Output('violin-chart', 'figure'),
    Input('bar-chart', 'clickData')
)
def update_violin(clickData):
    if clickData:
        selected = clickData['points'][0]['x']
        return generate_violin(selected)
    return generate_violin()
