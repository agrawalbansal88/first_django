from __future__ import unicode_literals

from django.db import models

# Create your models here.

class TradeModel(models.Model):
    order_execution_time = models.DateField()
    tradingsymbol = models.CharField(max_length=30)
    trade_type = models.CharField(max_length=5)
    quantity = models.FloatField(default=0.0)
    price = models.FloatField(default=0.0)
