from django.shortcuts import render, render_to_response
from personal.models import TradeModel

import pandas as pd
from StringIO import StringIO
import time

EXPECTED_INPUT_PARAMS = ['client_id', 'trade_date', 'order_execution_time', 'exchange', 'tradingsymbol', 'trade_type', 'quantity', 'price', 'order_id', 'trade_id', 'series']

def index(request):
    if request.method == "POST":
        paramFile = request.FILES['zerodha_file'].read()
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
    for tradesymbol in tradingsymbols:
        all_stock_data.append(get_analyzed_data(tradesymbol))
    return all_stock_data


def contact(request):
    trade_objs = TradeModel.objects.all()
    if request.method == "POST":
        selected_stock= request.POST.get('selected_stock')
        response = create_trade_specfic_response(selected_stock)
        return render(request, 'personal/show_trades.html', response)
    else:
        trade_objs = TradeModel.objects.all()
        tradingsymbols = sorted(set([trade_obj.tradingsymbol for trade_obj in trade_objs]))
        return render(request, 'personal/show_trades.html', {'tradingsymbols':tradingsymbols})



def create_trade_specfic_response(selected_stock):
    trade_dict = get_analyzed_data(selected_stock)
    trade_dict['Ankur'] = get_html(selected_stock)
    return trade_dict

def get_analyzed_data(selected_stock):
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

    trade_dict = {  'selected_trades': selected_trades,
                    'tradingsymbol':selected_stock,
                    'tradingsymbols':tradingsymbols,
                    'current_count': current_count,
                    'current_total_val': current_total_val,
                    'current_avg_price': current_avg_price,
                    'profit_booked':profit_booked}

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