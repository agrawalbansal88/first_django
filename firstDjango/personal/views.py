from django.shortcuts import render
from personal.models import TradeModel

import pandas as pd
from StringIO import StringIO

EXPECTED_INPUT_PARAMS = ['client_id', 'trade_date', 'order_execution_time', 'exchange', 'tradingsymbol', 'trade_type', 'quantity', 'price', 'order_id', 'trade_id', 'series']

def index(request):
    if request.method == "POST":
        paramFile = request.FILES['zerodha_file'].read()
        data_df = pd.read_csv(StringIO(paramFile))
        if list(data_df.columns.values) == EXPECTED_INPUT_PARAMS:
            process_data_df(data_df)
            parse_result = "<h4 style='color:MediumSeaGreen;'>Successfully Uploaded trade file...!!!</h4>"
            return render(request, 'personal/home.html', {"data_df": data_df.to_html(), 'parse_result': parse_result})
        else:
            parse_result = "<h4 style='color:Tomato;'>ERROR while processing trade file...!!!</h4>"
            return render(request, 'personal/home.html', {'parse_result':parse_result})
    else:
        return render(request, 'personal/home.html')




def contact(request):
    trade_objs = TradeModel.objects.all()
    if request.method == "POST":
        selected_stock= request.POST.get('selected_stock')
        response = create_trade_specfic_response(selected_stock)
        return render(request, 'personal/show_trades.html', response)
    else:
        trade_objs = TradeModel.objects.all()
        tradingsymbols = set([trade_obj.tradingsymbol for trade_obj in trade_objs])
        return render(request, 'personal/show_trades.html', {'tradingsymbols':tradingsymbols})



def create_trade_specfic_response(selected_stock):
    trade_objs = TradeModel.objects.all()
    selected_trades = [trade_obj.__dict__ for trade_obj in trade_objs if trade_obj.tradingsymbol == selected_stock]
    tradingsymbols = set([trade_obj.tradingsymbol for trade_obj in trade_objs])

    current_count = 0
    current_total_val = 0
    current_avg_price = 0
    for trade in selected_trades:
        if trade['trade_type'] == "buy":
            current_count += trade['quantity']
            current_total_val += trade['quantity'] * trade['price']
        else:
            current_count -= trade['quantity']
            current_total_val -= trade['quantity'] * trade['price']

    current_avg_price = current_total_val / current_count if current_count != 0 else 0.0
    profit_booked = current_total_val * -1 if current_count == 0 else "NA"
    current_total_val = current_total_val if current_count != 0 else 0.0
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