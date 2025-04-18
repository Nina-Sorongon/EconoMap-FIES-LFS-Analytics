import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# dash.register_page(__name__, path="/bivariate")

# Define the bivariate color bins map - using the notebook implementation
biv_bins_map = {
    "A3": "rgba(31,122,140,1)",  # #1f7a8c
    "B3": "rgba(27,73,101,1)",   # #1b4965
    "C3": "rgba(2,43,58,1)",     # #022b3a
    "A2": "rgba(112,162,136,1)", # #70a288
    "B2": "rgba(52,160,164,1)",  # #34a0a4
    "C2": "rgba(82,182,154,1)",  # #52b69a
    "A1": "rgba(190,233,232,1)", # #bee9e8
    "B1": "rgba(181,228,140,1)", # #b5e48c
    "C1": "rgba(95,168,211,1)",  # #5fa8d3
    "ZZ": "rgba(253,240,213,1)"  # #fdf0d5
}

# Load data
df_income_expenditure = pd.read_csv('Family Income and Expenditure.csv')
df_unemployment = pd.read_csv('LFS-PUF-December-2023.csv')
with open('ph_regions.json') as f:
    geojson = json.load(f)

# Define a function to get the most common value
def most_common(series):
    return series.mode()[0]

# Region mapping
region_mapping = {
    13: "NCR", 14: "CAR", 1: "I - Ilocos Region", 2: "II - Cagayan Valley",
    3: "III - Central Luzon", 4: "IV-A - CALABARZON", 17: "IV-B - MIMAROPA",
    5: "V - Bicol Region", 6: "VI - Western Visayas", 7: "VII - Central Visayas",
    8: "VIII - Eastern Visayas", 9: "IX - Zamboanga Peninsula", 10: "X - Northern Mindanao",
    11: "XI - Davao Region", 12: "XII - SOCCSKSARGEN", 16: "Region XIII  (Caraga)", 19: "ARMM"
}

# Region name corrections
region_corrections = {
    "IVB - MIMAROPA": "IV-B - MIMAROPA",
    "IVA - CALABARZON": "IV-A - CALABARZON",
    "IX - Zasmboanga Peninsula": "IX - Zamboanga Peninsula",
    " ARMM": "ARMM",
    "Caraga": "Region XIII  (Caraga)"
}

# Preprocess Data - Direct implementation from notebook
def preprocess_data():
    # Apply region corrections
    df_income_expenditure["Region"] = df_income_expenditure["Region"].replace(region_corrections)

    # Group income-expenditure data by region
    df_income_expenditure_grouped = (
        df_income_expenditure
        .groupby("Region")
        .agg({
            "Total Household Income": "mean",
            "Total Food Expenditure": "mean",
            "Household Head Highest Grade Completed": most_common
        })
        .reset_index()
    )

    # Rename columns for better understanding
    df_income_expenditure_grouped.columns = [
        "Region",
        "Mean Household Income",
        "Mean Household Expenditure",
        "Most Common HH Head Education"
    ]

    # Clean and compute unemployment rate from the LFS data
    df_lfs_clean = df_unemployment.dropna(subset=["PUFNEWEMPSTAT"])
    df_lfs_clean["PUFNEWEMPSTAT"] = df_lfs_clean["PUFNEWEMPSTAT"].astype(str).str.strip()
    df_lfs_clean = df_lfs_clean[df_lfs_clean["PUFNEWEMPSTAT"].str.isnumeric()]
    df_lfs_clean["PUFNEWEMPSTAT"] = df_lfs_clean["PUFNEWEMPSTAT"].astype(int)

    # Calculate unemployment rate
    labor_force = df_lfs_clean.groupby("PUFREG")["PUFNEWEMPSTAT"].count()
    unemployed = df_lfs_clean[df_lfs_clean["PUFNEWEMPSTAT"].isin([2, 3])].groupby("PUFREG")["PUFNEWEMPSTAT"].count()
    unemployed = unemployed.reindex(labor_force.index, fill_value=0)
    unemployment_rate = (unemployed / labor_force) * 100

    # Prepare the unemployment data
    df_unemployment_processed = unemployment_rate.reset_index()
    df_unemployment_processed.columns = ["Region_Code", "Unemployment Rate"]

    # Map region codes to region names in the unemployment data
    df_unemployment_processed["Region"] = df_unemployment_processed["Region_Code"].map(region_mapping)
    df_unemployment_processed = df_unemployment_processed.drop(columns=["Region_Code"], errors="ignore")

    # Merge datasets on the 'Region' column
    df_final_combined = pd.merge(df_income_expenditure_grouped, df_unemployment_processed, on="Region", how="outer")

    # Clean up and sort the merged dataset
    df_final_cleaned = df_final_combined[df_final_combined["Unemployment Rate"].notna()]
    df_final_cleaned = df_final_cleaned.sort_values(by="Mean Household Income", ascending=False)

    return df_final_cleaned

# Function to get bivariate choropleth color
def get_bivariate_choropleth_color(p1, p2):
    percentile_bounds1 = [0.33, 0.66, 1]  # variable 1
    percentile_bounds2 = [0.33, 0.66, 1]  # variable 2
    
    if p1 >= 0 and p2 >= 0:
        count = 0
        stop = False
        for percentile_bound_p1 in percentile_bounds1:
            for percentile_bound_p2 in percentile_bounds2:
                if (not stop) and (p1 <= percentile_bound_p1):
                    if (not stop) and (p2 <= percentile_bound_p2):
                        color = count
                        stop = True
                count += 1
    else:
        color = -1
    return color

# Create bivariate bins
def create_bivariate_bins(df):
    # Binning Household Income into 3 categories: Low, Medium, High
    df['Binned Household Income'] = pd.qcut(
        df['Mean Household Income'],
        q=3,  # 3 quantiles => 3 bins
        labels=['Low', 'Medium', 'High']
    )

    # Map education levels and income bins to numeric values for bivariate analysis
    education_map = {
        "Elementary Graduate": 0.25,
        "High School Graduate": 0.50,
        "College Graduate": 0.75
    }

    income_map = {
        "Low": 0.25,
        "Medium": 0.50,
        "High": 0.75
    }

    # Create numeric columns in the DataFrame
    df["EduVal"] = df["Most Common HH Head Education"].map(education_map)
    df["IncVal"] = df["Binned Household Income"].map(income_map)

    # Get bivariate numeric code for each row
    df["Bivariate Numeric Code"] = df.apply(
        lambda row: get_bivariate_choropleth_color(row["EduVal"], row["IncVal"]),
        axis=1
    )

    # Convert numeric code to bivariate bin labels
    numeric_to_bin = {
        0: "A1", 1: "A2", 2: "A3",
        3: "B1", 4: "B2", 5: "B3",
        6: "C1", 7: "C2", 8: "C3",
        -1: "ZZ"  # For invalid values
    }

    df["Bivariate Bin"] = df["Bivariate Numeric Code"].map(numeric_to_bin)
    
    return df

# Function to create legend
def create_legend(fig, colors):
    # Vertical position of top right corner (0: bottom, 1: top)
    top_rt_vt = 0.95
    # Horizontal position of top right corner (0: left, 1: right)
    top_rt_hz = 1.0
    
    # Reverse the order of colors
    legend_colors = colors[:]
    legend_colors.reverse()
    
    # Calculate coordinates for all nine rectangles
    coord = []
    
    # Adapt height to ratio to get squares
    width = 0.04
    height = 0.04 / 0.8
    
    # Start looping through rows and columns to calculate corners the squares
    for row in range(1, 4):
        for col in range(1, 4):
            coord.append({
                'x0': round(top_rt_vt - (col - 1) * width, 4),
                'y0': round(top_rt_hz - (row - 1) * height, 4),
                'x1': round(top_rt_vt - col * width, 4),
                'y1': round(top_rt_hz - row * height, 4)
            })
    
    # Create shapes (rectangle)
    for i, value in enumerate(coord):
        # Add rectangle
        fig.add_shape(go.layout.Shape(
            type='rect',
            fillcolor=legend_colors[i],
            line=dict(
                color='#f8f8f8',
                width=0,
            ),
            xref='paper',
            yref='paper',
            xanchor='right',
            yanchor='top',
            x0=coord[i]['x0'],
            y0=coord[i]['y0'],
            x1=coord[i]['x1'],
            y1=coord[i]['y1'],
        ))
    
    # Add text for first variable
    fig.add_annotation(
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='top',
        x=coord[8]['x1'],
        y=coord[8]['y1'],
        showarrow=False,
        text="Household Income" + ' →',
        font=dict(
            color='#000',
            size=12
        ),
        borderpad=1,
    )
    
    # Add text for second variable
    fig.add_annotation(
        xref='paper',
        yref='paper',
        xanchor='right',
        yanchor='bottom',
        x=coord[8]['x1'],
        y=coord[8]['y1'],
        showarrow=False,
        text="Education Level" + ' →',
        font=dict(
            color='#000',
            size=12,
        ),
        textangle=270,
        borderpad=1
    )
    
    return fig

# Function to generate bivariate map
def generate_bivariate_map(gdf, biv_bins_col, color_discrete, colors_scheme, custom_data_hover, map_title, map_subtitle):
    fig = px.choropleth(
        gdf,
        geojson=geojson,
        locations='Region',
        featureidkey='properties.REGION',
        color=biv_bins_col,
        height=900,
        color_discrete_map=color_discrete,
        custom_data=custom_data_hover,
    ).update_layout(
        paper_bgcolor='#fff9ed',
        plot_bgcolor='#fff9ed',
        geo=dict(
            bgcolor='#fff9ed',
            fitbounds="locations",
            visible=False  # make the base map invisible so it looks cleaner
        ),
        showlegend=False,
        title_x=0.05,
        title=dict(
            text=map_title,
            font=dict(
                size=24
            ),
        ),
        margin={"r":0, "t":85, "l":0, "b":0},
        map_style="carto-darkmatter",
        autosize=True,
        newshape_line_color="yellow",
        modebar_add=["drawline", "drawopenpath", "drawclosedpath", "drawcircle", "drawrect", "eraseshape"],
        modebar={"orientation":"h", "bgcolor":"white", "color":"black", "activecolor":"#9ed3cd"}
    ).update_traces(
        marker_line_width=0.5,  # width of the geo entity borders
        marker_line_color="#d1d1d1",  # color of the geo entity borders
        showscale=False,  # hide the colorscale
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Mean Household Income: ₱%{customdata[1]:,.2f}<br>" +
            "Education Level: %{customdata[2]}<extra></extra>"
        )
    )

    # Add legend
    fig = create_legend(fig, colors_scheme)

    return fig

# Process data for the map
df_final_cleaned = preprocess_data()
df_final_cleaned = create_bivariate_bins(df_final_cleaned)

# Map region names to match GeoJSON
geojson_region_mapping = {
    'NCR': 'Metropolitan Manila',
    'IV-A - CALABARZON': 'CALABARZON (Region IV-A)',
    'III - Central Luzon': 'Central Luzon (Region III)',
    'CAR': 'Cordillera Administrative Region (CAR)',
    'XI - Davao Region': 'Davao Region (Region XI)',
    'I - Ilocos Region': 'Ilocos Region (Region I)',
    'II - Cagayan Valley': 'Cagayan Valley (Region II)',
    'VII - Central Visayas': 'Central Visayas (Region VII)',
    'VI - Western Visayas': 'Western Visayas (Region VI)',
    'IV-B - MIMAROPA': 'MIMAROPA (Region IV-B)',
    'X - Northern Mindanao': 'Northern Mindanao (Region X)',
    'Region XIII  (Caraga)': 'Caraga (Region XIII)',
    'VIII - Eastern Visayas': 'Eastern Visayas (Region VIII)',
    'IX - Zamboanga Peninsula': 'Zamboanga Peninsula (Region IX)',
    'V - Bicol Region': 'Bicol Region (Region V)',
    'XII - SOCCSKSARGEN': 'SOCCSKSARGEN (Region XII)',
    'ARMM': 'Autonomous Region of Muslim Mindanao (ARMM)'
}

# Apply the mapping
df_final_cleaned['Region'] = df_final_cleaned['Region'].map(geojson_region_mapping)

# Layout
layout = html.Div(
    style={"backgroundColor": "#1E1E1E", "fontFamily": "Arial", "color": "white", "padding": "20px"},
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
            dcc.Loading(
                id="loading-bivariate-map",
                type="default",
                color="#00b4d8",
                children=[
                    dcc.Graph(id="bivariate-map-chart", style={
                        "width": "100%", 
                        "height": "600px",
                        "backgroundColor": "#333333"  # Dark background for the graph area
                    }),
                ]
            ),
        ])
    ]
)

# Callback
@dash.callback(
    Output("bivariate-map-chart", "figure"),
    Input("region-checklist", "value"),
    prevent_initial_call=False
)
def update_bivariate_map(selected_regions):
    # Ensure we have valid input
    if not selected_regions or len(selected_regions) == 0:
        raise PreventUpdate
        
    # Filter data based on selected regions
    df_filtered = df_final_cleaned[df_final_cleaned["Region"].isin(selected_regions)]
    
    if df_filtered.empty:
        raise PreventUpdate

    # Define hover data and titles
    custom_data_hover = [
        "Region",
        "Mean Household Income",
        "Most Common HH Head Education"
    ]
    map_title = "Regional Relationship Between Education and Income in the Philippines"
    map_subtitle = "Most Common Education Level vs. Average Household Income"

    # Generate Map
    try:
        fig = generate_bivariate_map(
            gdf=df_filtered,
            biv_bins_col="Bivariate Bin",
            color_discrete=biv_bins_map,
            colors_scheme=list(biv_bins_map.values()),
            custom_data_hover=custom_data_hover,
            map_title=map_title,
            map_subtitle=map_subtitle
        )
        
        # Force the figure to render properly
        fig.update_geos(fitbounds="locations", visible=False)
        return fig
    except Exception as e:
        print(f"Error generating bivariate map: {e}")
        raise PreventUpdate
