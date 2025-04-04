import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.CYBORG]
)
app.title = "EconoMap: FIES & LFS Analysis"

app.layout = dbc.Container([
    html.H1("EconoMap: FIES & LFS Analysis", style={
        "textAlign": "center",
        "color": "white", 
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "marginTop": "50px",
        "marginBottom": "20px"
    }),

    dbc.Nav([
        dbc.NavLink("Income Overview", href="/", active="exact", className="me-2"),
        dbc.NavLink("Region Filtering", href="/filter", active="exact", className="me-2"),
        dbc.NavLink("Regional Linking", href="/regional-linking", active="exact", className="me-2"),
        dbc.NavLink("Bivariate Map", href="/bivariate", active="exact", className="me-2"), 
    ], pills=True, justified=True, className="mb-4"),

    dbc.Container(dash.page_container, fluid=True)
], fluid=True)


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)