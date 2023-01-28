
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from rightmove_scraper.database_setup import engine
from sqlalchemy import create_engine
import plotly
import matplotlib.pyplot as plt
import plotly.graph_objs as go



engine = create_engine("mysql+pymysql://niklasgaertner@136.244.78.219:3306/rightmove")



app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    children=[
        html.H1(children="Amalie Dashboard",),
        html.P(
            children="love you love you love you",
        ),
        dcc.Graph(id='live-update-graph-scatter'),
        dcc.Interval(
            id='graph-update',
            interval=1*1000
        )
    ]
)

@app.callback(Output('live-update-graph-scatter', 'figure'),
              [Input('graph-update', 'n_intervals')])

def update_graph_scatter():
    with engine.begin() as con:
        df = pd.read_sql('select * from rightmove_data;', con)

    data = plotly.graph_objs.Scatter(
            x=list(df.BEDROOMS),
            y=list(df.PRICE),
            name='Scatter',
            mode= 'lines+markers'
            )

    return {'data': [data]}


if __name__ == '__main__':
    app.run_server(debug=False)