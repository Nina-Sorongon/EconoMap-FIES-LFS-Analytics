import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd

from utils.data_loader import get_final_dataframes

df_final_cleaned = get_final_dataframes()

dash.register_page(__name__, path="/regional-linking")

slider_min = 0
slider_max = 45
slider_step = 5
slider_marks = {i: f"{i}%" for i in range(slider_min, slider_max + 1, slider_step)}
all_unique_regions = sorted(df_final_cleaned["Region"].unique())

layout = html.Div(
    style={"backgroundColor": "#1e1e1e", "color": "white", "fontFamily": "Arial", "padding": "20px"},
    children=[
        html.H1("Regional Family Income, Expenditure, and Unemployment", style={"textAlign": "center"}),

        html.Div([
            html.Label("Filter by Unemployment Rate (%)", style={"fontWeight": "bold"}),
            dcc.RangeSlider(
                id='unemployment-slider',
                min=slider_min,
                max=slider_max,
                step=slider_step,
                value=[slider_min, slider_max],
                marks=slider_marks,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '80%', 'margin': 'auto', 'padding': '20px'}),
        
        html.Div([
            html.Label("Regions:", style={"fontWeight": "bold", "color": "white"}),  # Make label text white
            dcc.Checklist(
                id="region-checklist",
                options=[{"label": r, "value": r} for r in all_unique_regions],
                value=all_unique_regions,  # Initial value set to all regions
                labelStyle={"display": "block", "color": "white"},  # Make label text white
                inputStyle={"margin-right": "10px", "color": "white", "border-color": "white"},  # Ensure checkboxes are visible
                style={"color": "white"}
        )
        ], style={'width': '70%', 'margin': 'auto', 'padding': '20px'}),


        dcc.Graph(id='income-expenditure-chart', style={'height': '500px'}),
        dcc.Graph(id='unemployment-chart', style={'height': '500px'}),

        html.Div(id='info-display', style={
            'backgroundColor': '#2e2e2e',
            'padding': '20px',
            'margin': '30px auto',
            'width': '80%',
            'borderRadius': '8px',
            'color': 'white',
            'fontFamily': 'Arial'
        }),
    ]
)

# Callbacks
@dash.callback(
    Output("region-checklist", "options"),
    Output("region-checklist", "value"),
    Input("unemployment-slider", "value"),
    State("region-checklist", "value")
)
def update_region_checklist_options(unemp_range, currently_checked):
    low, high = unemp_range
    # Filter the dataset based on the unemployment range
    valid_df = df_final_cleaned[
        (df_final_cleaned["Unemployment Rate"] >= low) &
        (df_final_cleaned["Unemployment Rate"] <= high)
    ]
    
    # Get allowed regions after filtering
    allowed_regions = sorted(valid_df["Region"].unique())
    
    # Initialize the selected regions if it's empty
    if not currently_checked:
        currently_checked = allowed_regions  # Reset to filtered regions if no regions are selected

    # Update options and selected values for the checklist
    new_options = [{"label": r, "value": r} for r in allowed_regions]
    new_value = [r for r in currently_checked if r in allowed_regions]  # Ensure selected regions are valid

    return new_options, new_value


@dash.callback(
    Output('income-expenditure-chart', 'figure'),
    Output('unemployment-chart', 'figure'),
    Output('info-display', 'children'),
    Input('unemployment-slider', 'value'),
    Input('region-checklist', 'value'),
    Input('income-expenditure-chart', 'clickData')
)
def update_charts(unemp_range, selected_regions, click_data):
    low, high = unemp_range
    # Filter data by the selected unemployment rate range
    df_slider_filtered = df_final_cleaned[
        (df_final_cleaned["Unemployment Rate"] >= low) &
        (df_final_cleaned["Unemployment Rate"] <= high)
    ]
    # Filter further based on selected regions
    filtered_df = df_slider_filtered[df_slider_filtered["Region"].isin(selected_regions)]

    # Bar chart for Income and Expenditure
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=filtered_df["Region"],
        y=filtered_df["Mean Household Income"],
        name="Income",
        marker_color="#64dfdf"
    ))
    fig_bar.add_trace(go.Bar(
        x=filtered_df["Region"],
        y=filtered_df["Mean Household Expenditure"],
        name="Expenditure",
        marker_color="#80ffdb"
    ))
    fig_bar.update_layout(
        template="plotly_dark",
        barmode="group",
        title="Mean Income vs. Expenditure by Region",
        xaxis_title="Region",
        yaxis_title="PHP",
        font=dict(family="Arial")
    )

    # Line chart for Unemployment Rate
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=filtered_df["Region"],
        y=filtered_df["Unemployment Rate"],
        mode='lines+markers',
        marker=dict(size=8, color="#00b4d8"),
        line=dict(width=2, color="#00b4d8"),
        name="Unemployment Rate"
    ))
    fig_line.update_layout(
        template="plotly_dark",
        title="Unemployment Rate by Region",
        xaxis_title="Region",
        yaxis_title="%",
        font=dict(family="Arial")
    )

    # Info display text
    info_text = f"**Unemployment Range:** {low}% - {high}%  \n\n"
    info_text += "**Regions Shown:**\n" + "\n".join([f"- {r}" for r in filtered_df["Region"]]) + "\n\n"

    if click_data and click_data["points"]:
        region = click_data["points"][0]["x"]
        if region in filtered_df["Region"].values:
            row = filtered_df[filtered_df["Region"] == region].iloc[0]
            info_text += f"**Selected Region:** {region}  \n"
            info_text += f"Unemployment Rate: {row['Unemployment Rate']:.2f}%  \n"
            info_text += f"Income: PHP {row['Mean Household Income']:.2f}  \n"
            info_text += f"Expenditure: PHP {row['Mean Household Expenditure']:.2f}  \n"
    else:
        info_text += f"Average Income: PHP {filtered_df['Mean Household Income'].mean():.2f}  \n"
        info_text += f"Average Expenditure: PHP {filtered_df['Mean Household Expenditure'].mean():.2f}  \n"
        info_text += f"Average Unemployment: {filtered_df['Unemployment Rate'].mean():.2f}%  \n"

    return fig_bar, fig_line, dcc.Markdown(info_text)
