import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd

dash.register_page(__name__, path='/filter', name='Filtering by Region')

# Load and process
df = pd.read_csv("Family Income and Expenditure.csv")

def categorize_income(income):
    if income < 20000:
        return 'Low Income'
    elif 20000 <= income < 60000:
        return 'Lower Middle Income'
    elif 60000 <= income < 150000:
        return 'Upper Middle Income'
    else:
        return 'High Income'

df['Income Group'] = df['Total Household Income'].apply(categorize_income)

# Custom cool-toned color palette: dark blue → sky blue → light green
cool_palette = ['#0077b6', '#48cae4', '#90e0ef', '#b5ead7']

layout = html.Div([
    html.H2("Region-Based Income & Expenditure", style={
        "color": "white",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "marginBottom": "20px"
    }),

    html.Label("Select Region:", style={
        "color": "white",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "fontSize": "16px"
    }),

    dcc.Dropdown(
        id='region-filter',
        options=[{'label': r, 'value': r} for r in sorted(df['Region'].dropna().unique())],
        multi=True,
        placeholder="Choose region(s)...",
        style={
            "backgroundColor": "#2c2c2c",
            "color": "black",
            "border": "1px solid #666",
            "fontFamily": "Segoe UI, Arial, sans-serif"
        }
    ),

    dcc.Graph(id='income-bar-chart', style={"marginTop": "30px"}),
    dcc.Graph(id='expenditure-violin', style={"marginTop": "30px"})
], style={
    "padding": "20px",
    "backgroundColor": "#111",
    "minHeight": "100vh"
})


@dash.callback(
    Output('income-bar-chart', 'figure'),
    Output('expenditure-violin', 'figure'),
    Input('region-filter', 'value')
)
def update_charts(selected_regions):
    filtered_df = df if not selected_regions else df[df['Region'].isin(selected_regions)]

    income_fig = px.histogram(
        filtered_df, x='Income Group',
        color='Income Group',
        title="Income Distribution by Region",
        color_discrete_sequence=cool_palette,
        template='plotly_dark'
    )
    income_fig.update_layout(
        font=dict(family="Segoe UI, Arial, sans-serif", size=14),
        margin=dict(t=50, l=40, r=40, b=40)
    )

    expenditure_fig = px.violin(
        filtered_df, y='Total Food Expenditure', x='Income Group',
        box=True, points="all", color='Income Group',
        color_discrete_sequence=cool_palette,
        title="Food Expenditure by Income Group (Region Filtered)",
        template='plotly_dark'
    )
    expenditure_fig.update_layout(
        font=dict(family="Segoe UI, Arial, sans-serif", size=14),
        margin=dict(t=50, l=40, r=40, b=40)
    )

    return income_fig, expenditure_fig
