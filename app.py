
# --- Imports ---
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# --- Load and Clean Data ---
df = pd.read_csv("https://raw.githubusercontent.com/ChillakuruSaipranam/IMDB_Movies_Explorer/refs/heads/main/movies.csv")
df = df.dropna(subset=['Series_Title', 'Released_Year', 'IMDB_Rating', 'No_of_Votes', 'Genre', 'Certificate', 'Director'])
df['Released_Year'] = pd.to_numeric(df['Released_Year'], errors='coerce')
df['Gross'] = df['Gross'].replace(r'[\$,]', '', regex=True)
df['Gross'] = pd.to_numeric(df['Gross'], errors='coerce')
df = df.dropna(subset=['Released_Year']).copy()
df['Released_Year'] = df['Released_Year'].astype(int)
df['Main_Genre'] = df['Genre'].apply(lambda x: x.split(',')[0] if pd.notnull(x) else x)

available_genres = sorted(df['Main_Genre'].dropna().unique())
available_certificates = sorted(df['Certificate'].dropna().unique())
available_directors = sorted(df['Director'].dropna().unique())

# --- Initialize Dash ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

# --- Layout ---
app.layout = dbc.Container(fluid=True, children=[

    dbc.NavbarSimple(
        brand="🎬 IMDb Movies Explorer",
        brand_style={"fontSize": "28px"},
        color="dark",
        dark=True,
        className="mb-4"
    ),

    dbc.Row([

        dbc.Col([
            html.H4("Filters", className="text-light mb-3"),
            html.Label("Genre:", className="text-light"),
            dcc.Dropdown(id='genre-filter',
                         options=[{'label': g, 'value': g} for g in available_genres],
                         multi=True, placeholder="Select Genre"),
            html.Br(),
            html.Label("Certificate:", className="text-light"),
            dcc.Dropdown(id='certificate-filter',
                         options=[{'label': c, 'value': c} for c in available_certificates],
                         multi=True, placeholder="Select Certificate"),
            html.Br(),
            html.Label("Director:", className="text-light"),
            dcc.Dropdown(id='director-filter',
                         options=[{'label': d, 'value': d} for d in available_directors],
                         multi=True, placeholder="Select Director"),
            html.Br(),
            html.Label("Released Year Range:", className="text-light"),
            dcc.RangeSlider(id='year-slider', min=df['Released_Year'].min(), max=df['Released_Year'].max(), value=[2000, 2020], marks={str(year): str(year) for year in range(df['Released_Year'].min(), df['Released_Year'].max()+1, 5)}, tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("IMDb Rating Range:", className="text-light"),
            dcc.RangeSlider(id='rating-slider', min=0, max=10, step=0.1, value=[7, 10], marks={i: str(i) for i in range(0, 11)}, tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Gross Earnings Range ($):", className="text-light"),
            dcc.RangeSlider(id='gross-slider', min=0, max=df['Gross'].max() if 'Gross' in df.columns else 1e9, step=1e7, value=[0, 500e6], tooltip={"placement": "bottom", "always_visible": True}),
        ], width=3, style={"background-color": "#1a1a1a", "padding": "20px"}),

        dbc.Col([
            dbc.Row([dbc.Col(dcc.Graph(id="top10-movies-graph"), width=12)], className="mb-4"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="rating-vs-gross-graph"), width=6),
                dbc.Col(dcc.Graph(id="certificate-pie"), width=6),
            ], className="mb-4"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="genre-treemap"), width=6),
                dbc.Col(dcc.Graph(id="gross-trend-line"), width=6),
            ], className="mb-4"),
            dbc.Row([dbc.Col(dcc.Graph(id="heatmap-correlation"), width=12)], className="mb-4"),
            html.Hr(),
            html.H3("🎥 Compare Two Movies in Detail", className="text-light mb-3"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='movie-compare-1', options=[{'label': t, 'value': t} for t in df['Series_Title'].dropna().unique()], placeholder="Select First Movie"), width=6),
                dbc.Col(dcc.Dropdown(id='movie-compare-2', options=[{'label': t, 'value': t} for t in df['Series_Title'].dropna().unique()], placeholder="Select Second Movie"), width=6),
            ], className="mb-4"),
            dbc.Row([dbc.Col(html.Div(id='movie-comparison-output', className='text-light'), width=12)]),
            dbc.Row([dbc.Col(dcc.Graph(id='movie-comparison-visualization'), width=12)])
        ], width=9)
    ]),

    html.Hr(),
    html.P("Built by Sai Pranam | 2025", className="text-center text-muted mb-2"),
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
def update_graphs(genres, certs, directors, year_range, rating_range, gross_range):
    dff = df[(df['Released_Year'] >= year_range[0]) & (df['Released_Year'] <= year_range[1]) & (df['IMDB_Rating'] >= rating_range[0]) & (df['IMDB_Rating'] <= rating_range[1]) & (df['Gross'].between(gross_range[0], gross_range[1]))]
    if genres:
        dff = dff[dff['Main_Genre'].isin(genres)]
    if certs:
        dff = dff[dff['Certificate'].isin(certs)]
    if directors:
        dff = dff[dff['Director'].isin(directors)]

    top10 = dff.nlargest(10, 'IMDB_Rating')
    fig_top10 = px.bar(top10, x='Series_Title', y='IMDB_Rating', color='Main_Genre',
                       text='IMDB_Rating',
                       hover_data={"Gross":":$,.0f", "No_of_Votes":True, "Director":True},
                       title="Top 10 Movies by IMDb Rating")

    fig_scatter = px.scatter(dff, x='IMDB_Rating', y='Gross', color='Main_Genre', size='No_of_Votes', hover_data=['Series_Title', 'Director'], title="IMDb Rating vs Gross Earnings")

    fig_treemap = px.treemap(dff, path=['Main_Genre'], values='IMDB_Rating', color='IMDB_Rating', title="Treemap: Genre vs IMDb Rating")

    fig_pie = px.pie(dff, names='Certificate', title="Distribution of Movie Certificates")

    revenue = dff.groupby('Released_Year').agg({'Gross':'sum'}).reset_index()
    fig_line = px.line(revenue, x='Released_Year', y='Gross', markers=True, title="Total Gross Revenue Over Years")

    corr = dff[['IMDB_Rating', 'Gross', 'Released_Year']].corr()
    fig_heatmap = px.imshow(corr, text_auto=True, color_continuous_scale='Viridis', title="Correlation Between Rating, Gross, and Year")

    return fig_top10, fig_scatter, fig_treemap, fig_pie, fig_line, fig_heatmap

@app.callback(
    [Output('movie-comparison-output', 'children'),
     Output('movie-comparison-visualization', 'figure')],
    [Input('movie-compare-1', 'value'),
     Input('movie-compare-2', 'value')]
)
def compare_movies(movie1, movie2):
    if not movie1 or not movie2:
        return html.Div(), go.Figure()
    comparison = df[df['Series_Title'].isin([movie1, movie2])]
    cards = []
    for _, row in comparison.iterrows():
        cards.append(dbc.Card([
            dbc.CardBody([
                html.H4(row['Series_Title'], className="card-title"),
                html.P(f"Year: {row['Released_Year']}", className="card-text"),
                html.P(f"IMDb Rating: {row['IMDB_Rating']}", className="card-text"),
                html.P(f"Votes: {row['No_of_Votes']}", className="card-text"),
                html.P(f"Gross: ${row['Gross']:,}" if pd.notnull(row['Gross']) else "Gross: N/A", className="card-text"),
                html.P(f"Director: {row['Director']}", className="card-text"),
                html.P(f"Genre: {row['Genre']}", className="card-text"),
            ])
        ], color="dark", outline=True, className="mb-3"))

    fig_compare = px.bar(comparison, x='Series_Title', y='IMDB_Rating', color='Main_Genre',
                         text='IMDB_Rating',
                         hover_data=['Gross', 'No_of_Votes', 'Released_Year', 'Director', 'Genre'],
                         title="Comparison of Selected Movies")
    fig_compare.update_traces(textposition='outside')

    return dbc.Row([dbc.Col(card, width=6) for card in cards]), fig_compare


# --- Run Server ---
if __name__ == '__main__':
    app.title = "IMDb Dashboard"
    app.run(debug=False, host="0.0.0.0", port=8080)
