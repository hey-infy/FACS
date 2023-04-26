import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
from flask import Flask, render_template,request,redirect
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from alpha_vantage.techindicators import TechIndicators
import plotly.graph_objects as go
import requests
import plotly.express as px
from plotly.subplots import make_subplots
import ipywidgets as widgets
from IPython.display import display
API_key = 'J4SJ6FAAQG63WZLC'

app = Flask(__name__)
API_key = 'J4SJ6FAAQG63WZLC'


@app.route('/')
def index():
    
    stock_table = None

    # Fetching list of company names and stock tickers
    url = "https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=" + API_key
    stock_names = pd.read_csv(url)
    stock_names = stock_names[['name','symbol']].T.to_dict()
    return render_template("index.html", table = stock_table, stock_names = stock_names)


@app.route('/stock/report', methods=["GET",'POST'])
def fetch_stock_data():
    if request.method == 'POST':
        stock = request.form.get('company_name')
        ts = TimeSeries(key = API_key, output_format = 'pandas')
        data = ts.get_daily_adjusted(stock, outputsize= 'full')    
        f_data = data[0]
        #renaming columns
        f_data.rename(columns={'1. open':'Open', '2. high': 'High', '3. low':'Low', '4. close':'Close', '5. adjusted close': 'Adjusted Close', '6. volume':'Volume', '7. dividend amount':'Dividend Amount', '8. split coefficient':'Split Coefficient'}, inplace = True)
        f_data.head(3)
        #dropping unwanted columns
        f_data.drop(['Split Coefficient'], axis= 1, inplace=True)
        f_data.drop(['Dividend Amount'], axis = 1, inplace = True)
        f_data.drop(['Adjusted Close'], axis= 1, inplace= True)
        #making a column for Rise/Drop
        f_data['Rise/Drop'] = f_data['Open'] - f_data['Close']
        f_data.sort_index(inplace=True)
        #matching the TS data to SMA data
        f_data = f_data.loc['2015-01-09':]
        f_data_new = f_data.reset_index()
        # Initialize figure
        fig = go.Figure()

        # Add Traces

        fig.add_trace(
            go.Scatter(x=list(f_data_new.date),
                    y=list(f_data_new.High),
                    name="High",
                    line=dict(color="#33CFA5")))

        fig.add_trace(
            go.Scatter(x=list(f_data_new.date),
                    y=[f_data_new.High.mean()] * len(f_data_new.index),
                    name="High Average",
                    visible=False,
                    line=dict(color="#33CFA5", dash="dash")))

        fig.add_trace(
            go.Scatter(x=list(f_data_new.date),
                    y=list(f_data_new.Low),
                    name="Low",
                    line=dict(color="#F06A6A")))

        fig.add_trace(
            go.Scatter(x=list(f_data_new.date),
                    y=[f_data_new.Low.mean()] * len(f_data_new.index),
                    name="Low Average",
                    visible=False,
                    line=dict(color="#F06A6A", dash="dash")))

        # Add Annotations and Buttons
        high_annotations = [dict(x="2016-03-01",
                                y=f_data_new.High.mean(),
                                xref="x", yref="y",
                                text="High Average:<br> %.3f" % f_data_new.High.mean(),
                                ax=0, ay=-40),
                            dict(x=f_data_new.date[f_data_new.High.idxmax()],
                                y=f_data_new.High.max(),
                                xref="x", yref="y",
                                text="High Max:<br> %.3f" % f_data_new.High.max(),
                                ax=-40, ay=-40)]
        low_annotations = [dict(x="2015-05-01",
                                y=f_data_new.Low.mean(),
                                xref="x", yref="y",
                                text="Low Average:<br> %.3f" % f_data_new.Low.mean(),
                                ax=0, ay=40),
                        dict(x=f_data_new.date[f_data_new.High.idxmin()],
                                y=f_data_new.Low.min(),
                                xref="x", yref="y",
                                text="Low Min:<br> %.3f" % f_data_new.Low.min(),
                                ax=0, ay=40)]

        fig.update_layout(
            updatemenus=[
                dict(
                    active=0,
                    buttons=list([
                        dict(label="None",
                            method="update",
                            args=[{"visible": [True, False, True, False]},
                                {"title": stock,
                                    "annotations": []}]),
                        dict(label="High",
                            method="update",
                            args=[{"visible": [True, True, False, False]},
                                {"title": stock + " High",
                                    "annotations": high_annotations}]),
                        dict(label="Low",
                            method="update",
                            args=[{"visible": [False, False, True, True]},
                                {"title": stock + " Low",
                                    "annotations": low_annotations}]),
                        dict(label="Both",
                            method="update",
                            args=[{"visible": [True, True, True, True]},
                                {"title": stock + " High & Low",
                                    "annotations": high_annotations + low_annotations}]),
                    ]),
                )
            ])

        # Add range slider
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                            label="1m",
                            step="month",
                            stepmode="backward"),
                        dict(count=6,
                            label="6m",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="YTD",
                            step="year",
                            stepmode="todate"),
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        # Set title
        fig.update_layout(title_text=stock)  
        
    
        # Rise / Drop trend
        data = f_data.groupby(pd.Grouper(freq='M')).mean('Rise/Drop')    #change to make a function and add filter 
        fig_data = px.area(data, y = 'Rise/Drop', title = "Rise - Drop Trend",)
        fig_data.update_layout(title=dict(x=0.5))

        # Add range slider
        fig_data.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                            label="1m",
                            step="month",
                            stepmode="backward"),
                        dict(count=6,
                            label="6m",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="YTD",
                            step="year",
                            stepmode="todate"),
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )


        #adding horizontal line
        fig_data.add_shape(type='line', x0=0, x1=1, xref='paper', y0=0, y1=0, yref='y')

        #candle-Stick Chart
        cs_df = f_data
        cs_df = cs_df.reset_index()

        figure = make_subplots(specs=[[{"secondary_y": True}]] )
        figure.add_trace(go.Candlestick(
            x=cs_df['date'],
            open=cs_df['Open'],
            high=cs_df['High'],
            low=cs_df['Low'],
            close=cs_df['Close']), 
            secondary_y= True)

        # Add range slider
        figure.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                            label="1m",
                            step="month",
                            stepmode="backward"),
                        dict(count=6,
                            label="6m",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="YTD",
                            step="year",
                            stepmode="todate"),
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        figure.add_trace(go.Bar(x = cs_df["date"], y = cs_df["Volume"]), secondary_y= False)
        return render_template('report.html',stock=stock, fig1=fig.to_html(), fig2 = fig_data.to_html(), fig3 = figure.to_html())



if __name__ == "__main__":
    app.run(debug = True)
