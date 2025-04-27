# --- Imports ---
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# --- Load and Clean Data ---
df=pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRD4WRZfCs7hqW3yT3tRp2-YzYaqmy292_UIxHu9OQy0Fcg3AfTWt_JUq728F75-BZ13VkA38aPyUdH/pub?output=csv")

# Fix Released Year
df['Released_Year'] = pd.to_numeric(df['Released_Year'], errors='coerce')
df = df.dropna(subset=['Released_Year']).copy()  # <---- SAFE
df['Released_Year'] = df['Released_Year'].astype(int)

# Fix Gross Earnings
if 'Gross' in df.columns:
    df['Gross'] = df['Gross'].replace(r'[\$,]', '', regex=True)
    df['Gross'] = pd.to_numeric(df['Gross'], errors='coerce')

# --- Initialize Dash ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# --- Layout ---
app.layout = dbc.Container(fluid=True, children=[

    # Header
    dbc.Row([
        dbc.Col(html.H1("IMDb Movies Data Explorer", className="text-center text-primary mb-4"), width=12),
        dbc.Col(html.H5("Explore Success Factors: Ratings, Genres, Directors, Revenue", className="text-center text-secondary mb-4"), width=12),
    ]),

    # Filters + Main Dashboard
    dbc.Row([

        # Sidebar
        dbc.Col([
            html.H4("Filters", className="text-primary"),

            html.Label("Select Genre:"),
            dcc.Dropdown(id='genre-filter',
                         options=[{'label': g, 'value': g} for g in df['Genre'].dropna().unique()],
                         multi=True, placeholder="Select Genre"),
            html.Br(),

            html.Label("Select Certification:"),
            dcc.Dropdown(id='certificate-filter',
                         options=[{'label': c, 'value': c} for c in df['Certificate'].dropna().unique()],
                         multi=True, placeholder="Select Certificate"),
            html.Br(),

            html.Label("Select Director:"),
            dcc.Dropdown(id='director-filter',
                         options=[{'label': d, 'value': d} for d in df['Director'].dropna().unique()],
                         multi=True, placeholder="Select Director"),
            html.Br(),

            html.Label("Released Year Range:"),
            dcc.RangeSlider(id='year-slider',
                            min=df['Released_Year'].min(),
                            max=df['Released_Year'].max(),
                            value=[2000, 2020],
                            marks={str(year): str(year) for year in range(df['Released_Year'].min(), df['Released_Year'].max()+1, 5)},
                            tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),

            html.Label("IMDb Rating Range:"),
            dcc.RangeSlider(id='rating-slider',
                            min=0, max=10, step=0.1,
                            value=[7, 10],
                            marks={i: str(i) for i in range(0, 11)},
                            tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),

            html.Label("Gross Earnings Range ($):"),
            dcc.RangeSlider(id='gross-slider',
                            min=0, max=df['Gross'].max() if 'Gross' in df.columns else 1e9,
                            step=1e7,
                            value=[0, 500e6],
                            tooltip={"placement": "bottom", "always_visible": True}),
        ], width=3, style={"background-color": "#f8f9fa", "padding": "20px", "border-radius": "8px"}),

        # Main Graphs
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id="top10-movies-graph"), width=6),
                dbc.Col(dcc.Graph(id="rating-vs-gross-graph"), width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(id="genre-treemap"), width=6),
                dbc.Col(dcc.Graph(id="certificate-pie"), width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(id="gross-trend-line"), width=12),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(id="heatmap-correlation"), width=12),
            ], className="mb-4"),
        ], width=9),

    ]),

    # Movie Comparison
    html.Hr(),

    dbc.Row([
        dbc.Col(html.H3("Compare Two Movies Side-by-Side", className="text-primary text-center"), width=12),
    ]),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id='movie-compare-1',
                             options=[{'label': t, 'value': t} for t in df['Series_Title'].dropna().unique()],
                             placeholder="Select First Movie"), width=6),
        dbc.Col(dcc.Dropdown(id='movie-compare-2',
                             options=[{'label': t, 'value': t} for t in df['Series_Title'].dropna().unique()],
                             placeholder="Select Second Movie"), width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='movie-comparison-graph'), width=12),
    ]),

    # Footer
    html.Hr(),
    dbc.Row([
        dbc.Col(html.P("© 2025 | IMDb Movie Data Project | Built by [Your Name]", className="text-center text-muted"), width=12),
    ])
])

# --- Callbacks ---
@app.callback(
    [Output('top10-movies-graph', 'figure'),
     Output('rating-vs-gross-graph', 'figure'),
     Output('genre-treemap', 'figure'),
     Output('certificate-pie', 'figure'),
     Output('gross-trend-line', 'figure'),
     Output('heatmap-correlation', 'figure')],
    [Input('genre-filter', 'value'),
     Input('certificate-filter', 'value'),
     Input('director-filter', 'value'),
     Input('year-slider', 'value'),
     Input('rating-slider', 'value'),
     Input('gross-slider', 'value')]
)
def update_graphs(selected_genres, selected_certs, selected_directors, year_range, rating_range, gross_range):
    # Filter Data
    dff = df[
        (df['Released_Year'] >= year_range[0]) & (df['Released_Year'] <= year_range[1]) &
        (df['IMDB_Rating'] >= rating_range[0]) & (df['IMDB_Rating'] <= rating_range[1]) &
        (df['Gross'].between(gross_range[0], gross_range[1], inclusive='both') if 'Gross' in df.columns else True)
    ]

    if selected_genres:
        dff = dff[dff['Genre'].isin(selected_genres)]
    if selected_certs:
        dff = dff[dff['Certificate'].isin(selected_certs)]
    if selected_directors:
        dff = dff[dff['Director'].isin(selected_directors)]

    # Top 10 Movies
    top10 = dff.nlargest(10, 'IMDB_Rating')
    fig_top10 = px.bar(top10, x='Series_Title', y='IMDB_Rating', color='Genre',
                       text='IMDB_Rating', color_discrete_sequence=px.colors.qualitative.Plotly,
                       title="Top 10 IMDb Rated Movies")
    fig_top10.update_traces(textposition='outside')
    fig_top10.update_layout(yaxis=dict(range=[8.5, 9.8]))

    # Rating vs Gross
    fig_scatter = px.scatter(dff.sample(min(200, len(dff)), random_state=42),
                             x='IMDB_Rating', y='Gross', color='Genre', size='Gross',
                             title="IMDb Rating vs Gross Earnings",
                             color_discrete_sequence=px.colors.qualitative.Plotly)

    # Treemap of Genres
    fig_treemap = px.treemap(dff, path=['Genre'], values='IMDB_Rating', color='IMDB_Rating',
                             color_continuous_scale='Blues', title="Top Genres by IMDb Rating")

    # Certificate Pie Chart
    fig_pie = px.pie(dff, names='Certificate', title="Certification Distribution of Movies")

    # Revenue Trend Line
    revenue_yearly = dff.groupby('Released_Year', as_index=False)['Gross'].sum()
    fig_line = px.line(revenue_yearly, x='Released_Year', y='Gross', markers=True,
                       title="Box Office Revenue Trend Over Years")

    # Correlation Heatmap
    df_corr = dff[['IMDB_Rating', 'Gross', 'Released_Year']].dropna()
    corr = df_corr.corr()
    fig_heatmap = px.imshow(corr, text_auto=True, color_continuous_scale='Viridis',
                            title="Correlation Heatmap (Rating, Gross, Year)")

    return fig_top10, fig_scatter, fig_treemap, fig_pie, fig_line, fig_heatmap

@app.callback(
    Output('movie-comparison-graph', 'figure'),
    [Input('movie-compare-1', 'value'),
     Input('movie-compare-2', 'value')]
)
def compare_movies(movie1, movie2):
    if not movie1 or not movie2:
        return go.Figure()

    comp = df[df['Series_Title'].isin([movie1, movie2])]
    fig = px.bar(comp, x='Series_Title', y='IMDB_Rating', color='Genre',
                 text='IMDB_Rating', title="Movie Rating Comparison",
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_traces(textposition='outside')
    return fig

# --- Run ---
server = app.server  # <- ADD this line for Render hosting

if __name__ == "__main__":
    app.run_server(debug=True)

