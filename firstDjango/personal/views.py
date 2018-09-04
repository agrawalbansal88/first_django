from django.shortcuts import render
import pandas as pd
from StringIO import StringIO

def index(request):
    if request.method == "POST":
        paramFile = request.FILES['zerodha_file'].read()
        data_df = pd.read_csv(StringIO(paramFile))
        return render(request, 'personal/home.html', {"data_df":data_df.to_html()})
    else:
        return render(request, 'personal/home.html')

def contact(request):
    return render(request, 'personal/basic.html', {'content':['I am a good boy', 'am I?']})
