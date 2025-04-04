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
    """Function to create map
    Arguments:
        gdf (GeoPandas DataFrame): Geospatial data, index as location and geometry col with polygon data
        biv_bins_col (list: str): color scheme to use in the bivariate map, list length of 9
        color_discrete (list: str): Dictionary mapping bivariate bin values to colors.
        colors_scheme (list) : color scheme to use in bivariate map
        custom_data_hover (list: str): data to be used in hover, ex. ["Zipcode", "Client_Count", "Age", "VL"]
        map_title (string): title for map
        map_subtitle (string): subtitle for map
    Returns:
        Plotly Figure Object
    """
    fig = px.choropleth(
        gdf,
        geojson=geojson,
        locations='Region',
        featureidkey='properties.REGION',
        color=biv_bins_col,
        height=900,
        color_discrete_map=color_discrete,
        custom_data=custom_data_hover
    ).update_layout(
        paper_bgcolor='#fff9ed',
        plot_bgcolor='#fff9ed',
        geo=dict(
            bgcolor='#fff9ed',
            fitbounds="locations",
            visible=True  # make the base map invisible so it looks cleaner
        ),
        showlegend=False,
        title_x=0.05,
        title=dict(
            text=map_title,
            font=dict(size=24)
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
        showscale=False  # hide the colorscale
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Mean Household Income: ₱%{customdata[1]:,.2f}<br>" +
            "Education Level: %{customdata[2]}<br>" +
            "Unemployment Rate: %{customdata[3]:.1f}%<extra></extra>"
        )
    )

    # Add the bivariate legend
    fig = create_legend(fig, list(colors_scheme.values()))

    return fig
