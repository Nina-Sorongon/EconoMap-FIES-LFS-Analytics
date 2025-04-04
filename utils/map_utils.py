# map_utils.py

import plotly.express as px
import plotly.graph_objects as go

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
    "ZZ": "#fdf0d5"  # No Data
}

def create_legend(fig, colors):
    # Function to create legend shapes
    top_rt_vt = 0.95
    top_rt_hz = 1.0
    legend_colors = colors[:]
    legend_colors.reverse()
    
    coord = []
    width = 0.04
    height = 0.04 / 0.8
    for row in range(1, 4):
        for col in range(1, 4):
            coord.append({
                'x0': round(top_rt_vt - (col - 1) * width, 4),
                'y0': round(top_rt_hz - (row - 1) * height, 4),
                'x1': round(top_rt_vt - col * width, 4),
                'y1': round(top_rt_hz - row * height, 4)
            })

    for i, value in enumerate(coord):
        fig.add_shape(go.layout.Shape(
            type='rect',
            fillcolor=legend_colors[i],
            line=dict(color='#f8f8f8', width=0),
            xref='paper', yref='paper', xanchor='right', yanchor='top',
            x0=coord[i]['x0'], y0=coord[i]['y0'], x1=coord[i]['x1'], y1=coord[i]['y1'],
        ))

    return fig

def generate_bivariate_map(gdf, biv_bins_col, color_discrete, colors_scheme, custom_data_hover, map_title, map_subtitle, geojson):
    # Create a choropleth map with the necessary data
    fig = px.choropleth(
        gdf,
        geojson=geojson,
        locations='Region',  # The column in the dataframe to link to geojson
        color=biv_bins_col,
        color_discrete_map=color_discrete,
        hover_data=custom_data_hover
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        title=dict(text=map_title, x=0.5),
        geo=dict(showcoastlines=True, coastlinecolor="Black"),
        annotations=[dict(
            x=0.5, y=-0.1, xref="paper", yref="paper", text=map_subtitle,
            showarrow=False, font=dict(size=14)
        )],
        coloraxis_showscale=False
    )

    return fig
