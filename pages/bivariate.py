import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import json
import pandas as pd
from utils.bivariate_utils import preprocess_data, create_bivariate_bins
from utils.map_utils import generate_bivariate_map

dash.register_page(__name__, path="/bivariate")

# Define the bivariate color bins map
biv_bins_map = {
    "A1": "#e2f2e3",  # Light Green
    "A2": "#c1e0da",  # Light Blue
    "A3": "#9ec9dd",
    "B1": "#bad3af",
    "B2": "#a9d1b8",
    "B3": "#69adaf",
    "C1": "#88c685",
    "C2": "#6fb998",
    "C3": "#4c9e8b",
    "ZZ": "#fdf0d5"  # No Data or fallback
}

# Load data
df_income_expenditure = pd.read_csv('Family Income and Expenditure.csv')
df_unemployment = pd.read_csv('LFS-PUF-December-2023.csv')
with open('ph_regions.json') as f:
    geojson = json.load(f)

# Region mapping
region_mapping = {
    13: "NCR", 14: "CAR", 1: "I - Ilocos Region", 2: "II - Cagayan Valley",
    3: "III - Central Luzon", 4: "IV-A - CALABARZON", 17: "IV-B - MIMAROPA",
    5: "V - Bicol Region", 6: "VI - Western Visayas", 7: "VII - Central Visayas",
    8: "VIII - Eastern Visayas", 9: "IX - Zamboanga Peninsula", 10: "X - Northern Mindanao",
    11: "XI - Davao Region", 12: "XII - SOCCSKSARGEN", 16: "Region XIII  (Caraga)", 19: "ARMM"
}

# Preprocess Data
df_final_cleaned = preprocess_data(df_income_expenditure, df_unemployment, region_mapping)
df_final_cleaned = create_bivariate_bins(df_final_cleaned)

# Layout
layout = html.Div(
    style={"background-color": "#1E1E1E", "fontFamily": "Arial", "color": "white", "padding": "20px"},
    children=[
        html.H1("Bivariate Choropleth Map Dashboard", style={
            "textAlign": "center", 
            "fontFamily": "Segoe UI, Arial, sans-serif", 
            "marginTop": "50px", 
            "marginBottom": "20px",
            "color": "white"
        }),

        html.Div([
            html.Label("Select Regions:", style={
                "fontWeight": "bold", 
                "fontFamily": "Segoe UI, Arial, sans-serif", 
                "color": "white"
            }),
            dcc.Checklist(
                id="region-checklist",
                options=[{"label": region, "value": region} for region in df_final_cleaned["Region"].unique()],
                value=df_final_cleaned["Region"].unique().tolist(),
                style={
                    "fontFamily": "Segoe UI, Arial, sans-serif", 
                    "color": "white",
                    "backgroundColor": "#333333",  # Dark background for the checklist
                    "border": "none",
                    "padding": "5px"
                }
            ),
        ], style={"marginBottom": "30px"}),

        html.Div([
            dcc.Graph(id="bivariate-map-chart", style={
                "width": "100%", 
                "height": "600px",
                "backgroundColor": "#333333"  # Dark background for the graph area
            }),
        ])
    ]
)

# Callback
@dash.callback(
    Output("bivariate-map-chart", "figure"),
    Input("region-checklist", "value"),
)
def update_bivariate_map(selected_regions):
    # Filter data based on selected regions
    df_filtered = df_final_cleaned[df_final_cleaned["Region"].isin(selected_regions)]

    # Generate Map
    fig = generate_bivariate_map(df_filtered, geojson, biv_bins_map)

    return fig
