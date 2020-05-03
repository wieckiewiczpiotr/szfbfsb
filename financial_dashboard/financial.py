import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import pandas_datareader as pdr
import requests
import json
from datetime import datetime, timedelta

cmps_all = pd.read_csv('https://raw.githubusercontent.com/wieckiewiczpiotr/sample/master/WSE_metadata.csv', 
                       index_col='code')
cmps_all['name'] = cmps_all['name'].str.split(',', expand=True)[0].str.split(
    'for', expand=True)[1].str.lstrip()
cmps_all['name'] = cmps_all['name'].fillna(cmps_all.index.to_series())

cmps_current = cmps_all[cmps_all['to_date'] == cmps_all['to_date'].max()].copy()
cmps_outdated = cmps_all[(cmps_all['to_date'] != cmps_all['to_date'].max())].copy()

dropdown_opts_all = [{'label':row[0], 'value':index} 
                     for index, row in cmps_all.iterrows()]
dropdown_opts_current = [{'label':row[0], 'value':index} 
                         for index, row in cmps_current.iterrows()]

req = requests.get('http://api.nbp.pl/api/exchangerates/tables/a/')
curr_list = pd.DataFrame(data=json.loads(req.content)[0]['rates'])

dropdown_currs = [{'label':'{} ({})'.format(row[0], row[1]), 
                   'value':row[1]} for index, row in curr_list.iterrows()]

tab_style = {'line-height':'6vh', 
             'padding': '0', 
             'backgroundColor':'#35353b'}
tab_style_selected = {'line-height':'6vh', 
                      'padding': '0', 
                      'backgroundColor':'#434247', 
                      'color':'white'}
indices = ['WIG30', 'MWIG40', 'SWIG80', 'WIG_GAMES', 'WIG_BANKI', 'WIG_SPOZYW']
currencies = ['USD', 'EUR', 'CHF', 'GBP']
colors = px.colors.cyclical.HSV
colors_curr = px.colors.cyclical.Phase
text = '''
This dashboard is used to check the current and historical value of shares 
on the Warsaw Stock Exchange. It is possible to check several 
prices at the same time and compare with the candlestick chart. The top of 
the page  current values of selected stock indexes are displayed 
(refreshed every 2 minutes, given in real time) and current 
exchange rates, updated every hour.
'''
text_source = '''
#### Source for data
* index values: [webscraping from stooq.pl](https://stooq.pl/)
* exchange rates: [NBP web API](https://api.nbp.pl/) for historical data and 
[The Free Currency Converter API](https://free.currencyconverterapi.com/) 
for current data, updated every  hour
* main stock data: [Quandl](https://www.quandl.com/)
'''
text_curr = '''
Due to the fact that it is difficult to find a free source of 
historical exchange rates, this part of the dashboard has a specific 
date range up to only **one year back** from the last business day. 
In any case, it is still possible to choose from a wide range of 
currencies made available by the National Bank of Poland.
'''
text_markowitz = '''
## Markowitz portfolio selection
The model describes the relatioship between **risk** and **return** on 
given investment. By randomly selecting sets of weights for constructing a 
portfolio of selected stocks the most efficient portfolio of the given 
securities may be found. Each dot on the graph below symbolize a diffrent 
sets of weights of selected stocks in a investment portfolio. Generally 
speaking, the best portoflio is the one with the highest **Sharpe Ratio**. 
Return and volatility (risk) is calculated based on selected 
stocks and time period.

**Bear in mind that the more sets of weights and the longer 
time period the longer the graph will load.**
'''

app = dash.Dash(__name__)
server = app.server
app.layout = html.Div(children=[
    html.Div(children=[
        html.Div(
            className='eight columns div-graphs',
            children=[dcc.Interval(id='interval', interval=1000*60*2, n_intervals=0),
                      dcc.Interval(id='interval_curr', interval=1000*60*15, n_intervals=0),
                      html.Div([dcc.Loading(id='loading_indices', 
                                            children=[html.Div([dcc.Graph(id='indices')], 
                                                              style={'height':70, 
                                                                     'borderRadius': '15px',
                                                                     'border': '1px solid #35353b',
                                                                     'overflow': 'hidden'}),
                                                      html.Div(id='upd_indx',
                                                               style={'textAlign':'left'})
                                                     ])
                               ], style={'marginBottom':20}),
                      dcc.Tabs([
                          dcc.Tab(label='Stocks', children=[
                              html.Div([
                                  dcc.Loading(id='loading_line', 
                                              children=[html.Div([
                                                  dcc.Graph(id='line-graph')],
                                              style={'height':300, 
                                                     'marginTop':40})]
                                             )]),
                              html.Div([
                                  dcc.Loading(id='loading_candle', 
                                              children=[html.Div([
                                                  dcc.Graph(id='candle-graph')],
                                              style={'height':400, 
                                                     'marginTop':40})]
                                             )])], style=tab_style, 
                              selected_style=tab_style_selected),
                          dcc.Tab(label='Currencies', children=[
                              html.Div([dcc.Markdown(text_curr)], 
                                       style={'textAlign': 'justify', 
                                              'marginTop':'20px',
                                              'marginBottom':'30px'}),
                              html.Div([
                                  html.Div([dcc.Dropdown(
                                      id='menu_currs',
                                      options=dropdown_currs,
                                      multi=True,
                                      value=['USD', 'EUR', 'CHF', 'GBP'],
                                      placeholder='Select one or more currencies',
                                      style={'marginTop':'10px', 
                                             'backgroundColor': '#434247', 
                                             'color': 'black'})], 
                                           style={'textAlign': 'left'}),
                                  dcc.Loading(id='loading_curr_graph',
                                              children=[html.Div([
                                                  dcc.Graph(id='curr-graph')],
                                                  style={'marginTop':'40px'})]
                                             )])], 
                                  style=tab_style, 
                                  selected_style=tab_style_selected),
                          
                          dcc.Tab(label='Portfolio selection', children=[
                              html.Div([dcc.Markdown(text_markowitz)], 
                                       style={'textAlign': 'justify', 
                                              'marginTop':'20px',
                                              'marginBottom':'30px'}),
                              html.Div([
                                  dcc.Slider(id='slider',
                                             min=100,
                                             max=8000,
                                             step=100,
                                             value=3000)]),
                              
                              html.Div(id='slider_output', 
                                       style={'textAlign': 'left'}),
                              
                              dcc.Loading(id='loading_sharpe',
                                          children=[html.Div([
                                              dcc.Graph(id='sharpe')],
                                              style={'marginTop':'40px'})]
                                         )], 
                                  style=tab_style, 
                                  selected_style=tab_style_selected)
                      ], 
                          style={'height':'50px', 
                                 'fontSize': 20, 
                                 'marginTop':'1px'},
                          colors={'border': '#434247', 
                                  'primary': 'red', 
                                  'background': '#212020'})], 
            style={'textAlign': 'center'}), 
        html.Div(
            className='four columns div-controls controls',
            children=[dcc.Loading(id='loading_currencies', 
                                  children=html.Div([dcc.Graph(id='currencies')], 
                                                    style={'height':60, 
                                                           'marginTop': 5})),
                      html.H1("Investor's dashboard"), 
                      html.Div(dcc.Markdown(text), style={'textAlign':'justify'}),
                      html.Div(
                          dcc.DatePickerRange(
                              id='date-picker',
                              min_date_allowed=cmps_all['to_date'].min(),
                              max_date_allowed=datetime.today().date(),
                              start_date=datetime.today().date()-timedelta(days=365),
                              end_date=datetime.today().date(),
                              display_format='DD MMM YYYY',
                              style={'marginTop':'30px', 
                                     'marginBottom': '20px'}), 
                          style={'textAlign':'center'}),
                      html.Div(
                          html.Label(['Select one or multiple stocks',
                                      dcc.Dropdown(
                                      id='dropdown',
                                      options=dropdown_opts_current,
                                      multi=True,
                                      value=['KGHM', 'KRUK', 'TSGAMES'],
                                      placeholder='Select one or more companies',
                                      style={'marginTop':'10px', 
                                             'backgroundColor': '#35353b', 
                                             'color': 'black'})]), 
                          style={'marginTop':'25px'}),
                      html.Div(
                          dcc.Checklist(
                              id='check',
                              options=[
                                  {'label': 'Show historically listed companies in the menu above', 
                                   'value': 'all'}],
                              labelStyle={'display': 'inline-block'},
                              style={'marginTop':'15px'})),
                      html.Div(
                          html.Label(['Choose one of the stocks above for the candlestick chart',
                                      dcc.Dropdown(
                                      id='candle_dropdown',
                                      value='KRUK',
                                      placeholder='Select a company',
                                      style={'marginTop':'10px', 
                                             'color': 'black'})]), 
                          style={'marginTop':'30px'}),
                      html.Div([html.Button(id='apply_button', 
                                            children='Apply changes', 
                                            n_clicks=0,
                                            style={'fontSize': 22})],
                               style={'textAlign': 'center', 
                                      'marginTop':'30px',
                                      'marginBottom':'10px'}),
                      html.Div([dcc.Markdown(text_source)], 
                               style={'textAlign': 'justify',
                                      'marginBottom':'10px',
                                      'marginTop':'70px'})])])])
#--------------------------------------------------------------------------------------------------------------
#callback for updating menu for candlestick chart
@app.callback(Output('candle_dropdown', 'options'),
              [Input('dropdown', 'value')])
def update_candle_menu(value):
    options = [{'label':tick, 'value':tick} for tick in value]
    return options

#callback for showing last update
@app.callback(Output('upd_indx', 'children'),
              [Input('interval', 'n_intervals')])
def update_upd_indx(n):
    return 'Last update: {}'.format(datetime.now().strftime('%H:%M:%S'))

#callback for updating indices top of the app
@app.callback(Output('indices', 'figure'),
              [Input('interval', 'n_intervals')])
def update_indices(n):
    rates = []
    changes = []
    traces = []
    try:
        req = requests.get("https://stooq.pl/t/?i=528")
        soup = BeautifulSoup(req.text, 'html.parser')
        for index in indices:
            rates.append(float(soup.find(text=index).next_element.next_sibling.text))
            try:
                changes.append(float(soup.find(text=index).next_element.next_sibling.next_sibling.next_sibling.text))
            except:
                continue

        if len(changes) == len(indices):
            for number, index, rate, change in zip(range(len(indices)), indices, rates, changes):
                traces.append(go.Indicator(
                    mode='number+delta',
                    title=index,
                    title_font_size=14,
                    number_font_size=20,
                    value=rate,
                    delta={'reference': rate-change, 
                           'relative': True, 
                           'valueformat': '.2%'},
                    domain={'row': 1, 'column': number}))
        else:
            for number, index, rate in zip(range(len(indices)), indices, rates):
                traces.append(go.Indicator(
                    mode='number',
                    title=index,
                    title_font_size=14,
                    number_font_size=20,
                    value=rate,
                    domain={'row': 1, 
                            'column': number}))
        figure = {'data': traces,
                  'layout': go.Layout(
                      grid={'rows': 1, 
                            'columns': len(indices), 
                            'pattern': "independent"},
                      margin=dict(t=30, b=0, l=0, r=0),
                      plot_bgcolor='#35353b',
                      paper_bgcolor='#35353b',
                      font={'color': '#d8d8d8'},
                      height=70)}
        return figure
    
    except:  
        try:
            inds = ['WIG', 'WIG20', 'MWIG40', 'SWIG80', 'WIG_ODZIEZ', 'WIG_LEKI']
            traces = []
            for index, number in zip(inds, range(len(inds))):
                code = 'WSE/' + index
                df = pdr.get_data_quandl(
                    code, 
                    api_key='fHsXs9kzqak6UF1haCww', 
                    start=datetime.today().date()-timedelta(days=5))
                traces.append(go.Indicator(
                        mode='number',
                        title=index,
                        title_font_size=14,
                        number_font_size=20,
                        value=df['Close'][0],
                        domain={'row': 1, 
                                'column': number}))
                figure = {'data': traces,
                      'layout': go.Layout(
                          grid={'rows': 1, 
                                'columns': len(inds), 
                                'pattern': "independent"},
                          margin=dict(t=30, b=0, l=0, r=0),
                          plot_bgcolor='#35353b',
                          paper_bgcolor='#35353b',
                          font={'color': '#d8d8d8'},
                          height=70)}
            return figure
        except:
            figure = {
                'data': [go.Indicator(title='Could not connect to stooq to get index data',
                                      title_font_size=20,
                                      number_font_size=1)],
                'layout': go.Layout(
                          plot_bgcolor='#35353b',
                          paper_bgcolor='#35353b',
                          font={'color': 'tomato'},
                          height=70)}
            return figure

#callback for updating exchange rates at the top of the app
@app.callback(Output('currencies', 'figure'),
              [Input('interval_curr', 'n_intervals')])
def update_exchange_rates(n):
    traces = []
    try:
        req1 = requests.get('https://free.currconv.com/api/v7/convert?q=USD_PLN,EUR_PLN&compact=ultra&apiKey=ed6303b119a9753725a8')
        req2 = requests.get('https://free.currconv.com/api/v7/convert?q=CHF_PLN,GBP_PLN&compact=ultra&apiKey=ed6303b119a9753725a8')
        usd = json.loads(req1.content)['USD_PLN']
        eur = json.loads(req1.content)['EUR_PLN']
        chf = json.loads(req2.content)['CHF_PLN']
        gbp = json.loads(req2.content)['GBP_PLN']
        curr = [usd, eur, chf, gbp]

        for name, rate, number in zip(currencies, curr, range(len(currencies))):
            traces.append(go.Indicator(
                mode='number',
                title=name,
                title_font_size=14,
                number_font_size=20,
                value=rate,
                number_valueformat = '.5f',
                domain={'row': 1, 'column': number}))

        figure = {'data': traces,
                  'layout': go.Layout(
                      grid={'rows': 1, 
                            'columns': len(currencies), 
                            'pattern': "independent"},
                      margin=dict(t=23, b=0, l=0, r=0),
                      plot_bgcolor='#35353b',
                      paper_bgcolor='#35353b',
                      font={'color': '#d8d8d8'},
                      height=60)}
        return figure
    except:
        try:
            req = requests.get('http://api.nbp.pl/api/exchangerates/tables/a/')
            usd = json.loads(req.content)[0]['rates'][1]['mid']
            eur = json.loads(req.content)[0]['rates'][7]['mid']
            chf = json.loads(req.content)[0]['rates'][9]['mid']
            gbp = json.loads(req.content)[0]['rates'][10]['mid']
            curr = [usd, eur, chf, gbp]

            for name, rate, number in zip(currencies, curr, range(len(currencies))):
                traces.append(go.Indicator(
                    mode='number',
                    title=name,
                    title_font_size=14,
                    number_font_size=20,
                    value=rate,
                    number_valueformat = '.4f',
                    domain={'row': 1, 'column': number}))

            figure = {'data': traces,
                      'layout': go.Layout(
                          grid={'rows': 1, 
                                'columns': len(currencies), 
                                'pattern': "independent"},
                          margin=dict(t=23, b=0, l=0, r=0),
                          plot_bgcolor='#35353b',
                          paper_bgcolor='#35353b',
                          font={'color': '#d8d8d8'},
                          height=60)}
            return figure
        
        except:
            figure = {
                'data': [go.Indicator(title='Could not connect to API to get exchange rates data',
                                      title_font_size=15,
                                      number_font_size=1)],
                'layout': go.Layout(
                          plot_bgcolor='#35353b',
                          paper_bgcolor='#35353b',
                          font={'color': 'tomato'},
                          height=70)}
            return figure

#callback for updating main ticks dropdown menu
@app.callback(Output('dropdown', 'options'),
              [Input('check', 'value')])
def update_dropdown(value):
    if value == None or len(value) == 0:
        return dropdown_opts_current
    else:
        return dropdown_opts_all

@app.callback(Output('slider_output', 'children'),
              [Input('slider', 'value')])
def update_output(value):
    return 'Number of sets: {}'.format(value)
    
#callback for updating main time-series graph
@app.callback(Output('line-graph', 'figure'),
              [Input('apply_button', 'n_clicks')],
              [State('dropdown', 'value'),
               State('date-picker', 'start_date'),
               State('date-picker', 'end_date')])
def update_line(n, ticks, start_date, end_date):
    traces = []
    for name, color in zip(ticks, colors):
        tick = 'WSE/' + name
        df = pdr.get_data_quandl(tick, 
                                 api_key='fHsXs9kzqak6UF1haCww', 
                                 start=start_date, 
                                 end=end_date)
        traces.append({'x': df.index, 
                       'y': df['Close'], 
                       'name': name, 
                       'mode': 'lines',
                       'line': dict(color=color)
                      })
    figure = {'data': traces,
              'layout': {'height': 300,
                      'title': 'Stock chart for {}'.format(', '.join(ticks)),
                      'yaxis': {'gridcolor': '#35353b'},
                      'xaxis': {'gridcolor': '#35353b'},
                      'plot_bgcolor': '#434247',
                      'paper_bgcolor': '#434247',
                      'margin': dict(t=40, b=30, l=60, r=60),
                      'font': {'color': '#d8d8d8'}}}
    return figure

#callback for updating candlestick graph
@app.callback(Output('candle-graph', 'figure'),
              [Input('apply_button', 'n_clicks')],
              [State('candle_dropdown', 'value'),
               State('date-picker', 'start_date'),
               State('date-picker', 'end_date')])
def update_candle(n, tick, start_date, end_date):
    code = 'WSE/' + tick
    df = pdr.get_data_quandl(code, 
                             api_key='fHsXs9kzqak6UF1haCww', 
                             start=start_date, 
                             end=end_date)
    figure = {'data':[go.Candlestick(
        x=df.index,
        open=df['Open'],
        close=df['Close'],
        low=df['Low'], 
        high=df['High'],
        increasing_line_color= 'lime', 
        decreasing_line_color= 'red')],
             'layout': go.Layout(height=350,
                                 title='Candlestick chart for {}'.format(tick),
                                 plot_bgcolor='#434247',
                                 paper_bgcolor='#434247',
                                 yaxis={'gridcolor': '#35353b'},
                                 xaxis={'gridcolor': '#35353b'},
                                 font={'color': '#d8d8d8'},
                                 margin=dict(t=30, b=0, l=60, r=60))}
    return figure

#callback for updating currencies chart
@app.callback(Output('curr-graph', 'figure'),
              [Input('menu_currs', 'value')])
def update_curr_chart(currs):
    traces = []
    for curr, color in zip(currs, colors_curr):
        req = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/{}/{}/{}/'.format(
            curr,
            datetime.today().date()-timedelta(days=364), 
            datetime.today().date()))
        df = pd.DataFrame(data=json.loads(req.content)['rates'])

        traces.append({'x': df['effectiveDate'], 
                       'y': df['mid'], 
                       'name': curr, 
                       'mode': 'lines',
                       'line': dict(color=color)})
    figure = {'data': traces,
              'layout': {
                  'title': 'Echange rates for {}'.format(', '.join(currs)),
                  'yaxis': {'gridcolor': '#35353b'},
                  'xaxis': {'gridcolor': '#35353b'},
                  'plot_bgcolor': '#434247',
                  'paper_bgcolor': '#434247',
                  'margin': dict(t=30, b=30, l=60, r=60),
                  'font': {'color': '#d8d8d8'}}}
    return figure
#callback for updating currencies chart
@app.callback(Output('sharpe', 'figure'),
              [Input('apply_button', 'n_clicks')],
              [State('dropdown', 'value'),
               State('slider', 'value'),
               State('date-picker', 'start_date'),
               State('date-picker', 'end_date')
              ])
def update_sharpe(n, ticks, tries, start_date, end_date):
    if len(ticks) >= 2:
        df = pd.DataFrame()
        ret_arr = np.zeros(tries)
        vol_arr = np.zeros(tries)
        sr_arr = np.zeros(tries)

        for name in ticks:
            tick = 'WSE/' + name
            df_tick = pdr.get_data_quandl(tick, 
                                          api_key='fHsXs9kzqak6UF1haCww', 
                                          start=start_date, 
                                          end=end_date)
            df_tick.rename({'Close': name}, axis=1, inplace=True)
            df = df.join(df_tick[name], how='outer')

        logs = np.log(df/df.shift(-1))
        all_weights = np.zeros((tries, len(logs.columns)))

        for i in range(tries):
            weights = np.array(np.random.random(len(logs.columns)))
            weights = weights/np.sum(weights)
            all_weights[i,:] = weights
            ret_arr[i] = np.sum(logs.mean() * weights * len(logs))
            vol_arr[i] = np.sqrt(np.dot(weights.T, np.dot(logs.cov() * len(logs), weights)))
            sr_arr[i] = ret_arr[i] / vol_arr[i]

        weights_as_string = []
        for weight in all_weights:
            weights_as_string.append(', '.join(str(round(i, 3)) for i in weight))

        df = pd.DataFrame({'returns': ret_arr,
                           'volatility': vol_arr,
                           'sharpe': sr_arr,
                           'weights': weights_as_string})

        figure = px.scatter(df, x='volatility', 
                            y='returns', 
                            color='sharpe',
                            color_continuous_scale='RdPu_r',
                            hover_data=['weights'])
        
        figure.update_traces(marker=dict(size=9, line=dict(width=1)))

        figure.update_layout(
                          title='Portfolio allocation for {}'.format(', '.join(ticks)),
                          yaxis={'gridcolor': '#35353b'},
                          xaxis={'gridcolor': '#35353b'},
                          xaxis_title='Volatility',
                          yaxis_title='Returns',
                          plot_bgcolor='#434247',
                          paper_bgcolor='#434247',
                          margin=dict(t=40, b=30, l=60, r=60),
                          font={'color': '#d8d8d8'})
        return figure