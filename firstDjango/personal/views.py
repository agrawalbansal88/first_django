from __future__ import print_function
from django.shortcuts import render, render_to_response
from personal.models import TradeModel

import pandas as pd
from StringIO import StringIO
import time

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

EXPECTED_INPUT_PARAMS = ['client_id', 'trade_date', 'order_execution_time', 'exchange', 'tradingsymbol', 'trade_type', 'quantity', 'price', 'order_id', 'trade_id', 'series']

def index(request):
    if request.method == "POST":
        if request.FILES:
            paramFile = request.FILES['zerodha_file'].read()
        else:
            paramFile = get_tradebook_or_PnL_from_zerodha()
        data_df = pd.read_csv(StringIO(paramFile))
        if list(data_df.columns.values) == EXPECTED_INPUT_PARAMS:
            process_data_df(data_df)
            parse_result = "<h4 style='color:MediumSeaGreen;'>Successfully Uploaded trade file...!!!</h4>"
            return render(request, 'personal/home.html', {"data_df": data_df.to_html(),
                                                          'parse_result': parse_result,
                                                          'all_stock_data':all_trade_data()})
        else:
            parse_result = "<h4 style='color:Tomato;'>ERROR while processing trade file...!!!</h4>"
            return render(request, 'personal/home.html', {'parse_result':parse_result})
    else:
        return render(request, 'personal/home.html', {'all_stock_data':all_trade_data()})

def all_trade_data():
    trade_objs = TradeModel.objects.all()
    tradingsymbols = sorted(set([trade_obj.tradingsymbol for trade_obj in trade_objs]))
    all_stock_data = []
    all_live_data = {}#get_live_data()

    for tradesymbol in tradingsymbols:
        all_stock_data.append(get_analyzed_data(tradesymbol, all_live_data))
    return all_stock_data


def contact(request):

    trade_objs = TradeModel.objects.all()
    if request.method == "POST":
        selected_stock= request.POST.get('selected_stock')
        all_live_data = get_live_data()
        response = create_trade_specfic_response(selected_stock, all_live_data)
        return render(request, 'personal/show_trades.html', response)
    else:
        trade_objs = TradeModel.objects.all()
        tradingsymbols = sorted(set([trade_obj.tradingsymbol for trade_obj in trade_objs]))
        return render(request, 'personal/show_trades.html', {'tradingsymbols':tradingsymbols})



def create_trade_specfic_response(selected_stock, all_live_data):
    trade_dict = get_analyzed_data(selected_stock, all_live_data)
    trade_dict['Ankur'] = get_html(selected_stock)
    return trade_dict

def get_analyzed_data(selected_stock, all_live_data):
    trade_objs = TradeModel.objects.all()
    selected_trades = [trade_obj.__dict__ for trade_obj in trade_objs if trade_obj.tradingsymbol == selected_stock]

    tradingsymbols = sorted(set([trade_obj.tradingsymbol for trade_obj in trade_objs]))

    new_trade_list = []
    for trade in selected_trades:
        for i in range(int(trade['quantity'])):
            new_trade_list.append((trade['trade_type'], trade['price'], trade['order_execution_time']))

    trade_vals=[]
    profit_booked = 0
    for (trade_type, price, _) in new_trade_list:
        if trade_type == "buy":
            trade_vals.append(price)
        else:
            if trade_vals == []:continue
            buy_val = trade_vals.pop()
            profit_booked += price - buy_val

    current_count = len(trade_vals)
    current_total_val = round(sum(trade_vals),2)
    current_avg_price = round(current_total_val/current_count,2) if current_count != 0 else 0.0
    live_price =  float(all_live_data[selected_stock]) if selected_stock in all_live_data else 0
    current_val = live_price*current_count
    profit_loss = current_val - current_total_val
    if profit_loss >=0:
        profit_loss = "<h5 style='color:MediumSeaGreen;'>{}</h4>".format(profit_loss)
    else:
        profit_loss = "<h5 style='color:Tomato ;'>{}</h4>".format(profit_loss)

    trade_dict = {  'selected_trades': selected_trades,
                    'tradingsymbol':selected_stock,
                    'tradingsymbols':tradingsymbols,
                    'current_count': current_count,
                    'current_total_val': current_total_val,
                    'current_avg_price': current_avg_price,
                    'profit_booked':profit_booked,
                    'live_price':live_price,
                    'current_val': current_val,
                    'profit_loss':profit_loss}

    return trade_dict

def process_data_df(data_df):
    TradeModel.objects.all().delete()
    for _, row in data_df.iterrows():
        order_execution_time = row['order_execution_time'].split('T')[0]
        tradingsymbol = row['tradingsymbol']
        trade_type = row['trade_type']
        quantity = row['quantity']
        price = row['price']
        trade_obj = TradeModel(order_execution_time=order_execution_time,
                               tradingsymbol=tradingsymbol,
                               trade_type=trade_type,
                               quantity=quantity,
                               price=price)
        trade_obj.save()


#KEY: 125NKNLM9FJ2XONC https://www.alphavantage.co/support/#api-key
#KEY: q9tVsdxDY9RUPMJafHbF https://www.quandl.com/
#KEy: 125NKNLM9FJ2XONC https://www.alphavantage.co/support/#api-key
#https://github.com/madhurrajn

def get_html(selected_stock):
    from nvd3 import lineWithFocusChart, scatterChart, lineChart
    trade_objs = TradeModel.objects.all()
    selected_trades = [trade_obj.__dict__ for trade_obj in trade_objs if trade_obj.tradingsymbol == selected_stock]

    # chart = lineWithFocusChart(name='lineWithFocusChart', x_is_date=True, x_axis_format="%d %b %Y", height=400, width=1000)
    chart = scatterChart(name='scatterChart', x_is_date=True, x_axis_format="%d %b %Y", height=400, width=1000)
    xdata = [1491004800000]
    ydata = [None]
    ydata1 = [None]
    for trade in selected_trades:
        xdata.append(int(trade['order_execution_time'].strftime('%s')+"000"))
        if trade['trade_type'] == "buy":
            ydata.append(trade['price'])
            ydata1.append(None)
        else:
            ydata.append(None)
            ydata1.append(trade['price'])

    xdata.append(int(round(time.time() * 1000)))
    ydata.append(None)
    ydata1.append(None)

    extra_serie = {"tooltip": {"y_start": "", "y_end": " balls"},
                   "date_format": "%d %b %Y"}
    kwargs = {'size': '50'}
    chart.add_serie(name="BUY", y=ydata, x=xdata, extra=extra_serie, **kwargs)
    chart.add_serie(name="SELL", y=ydata1, x=xdata, extra=extra_serie, **kwargs)

    chart.buildhtml()
    return chart.htmlcontent

def get_live_data():
    #https://developers.google.com/sheets/api/quickstart/python
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    store = file.Storage('/Users/ankuragr/token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('/Users/ankuragr/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    #SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    SPREADSHEET_ID = '1euQ8Rt2pssNSRoN7yXNhfDTYmfS4sL_nrz9nttS8cnE'
    RANGE_NAME = 'BSE!A2:B'
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    else:
        return { row[0]:row[1]for row in values if row[1] != "#N/A"}


def get_tradebook_or_PnL_from_zerodha():
    import webbrowser
    import os
    import time

    DOWNLOADED_FILE_PATH = "/Users/ankuragr/Downloads/YN1586_tradebook.csv"
    RETRY_COUNT = 15
    if os.path.exists(DOWNLOADED_FILE_PATH):
        os.remove(DOWNLOADED_FILE_PATH)

    chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    url = 'https://console.zerodha.com/api/tradebook/?segment=EQ&tradingsymbol=&from=2017-04-01&to=2018-09-10&download=1'
    val = webbrowser.get(chrome_path).open(url)
    if val:
        count = 0
        while not os.path.exists(DOWNLOADED_FILE_PATH) and count < RETRY_COUNT:
            time.sleep(1)
            count += 1
        if not os.path.exists(DOWNLOADED_FILE_PATH): return None
        with open(DOWNLOADED_FILE_PATH, "rb") as f:
            data = f.read()
            return data
    return None