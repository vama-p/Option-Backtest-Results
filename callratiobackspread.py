# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 13:26:58 2025

@author: fcamv
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 10:39:30 2024

@author: fcamv

This strategy is an intraday strategy
SCRIPT: BankNifty
Entry: Strangle at 9:15
Exit: Stop loss 15% of combined premium/ 15:15
Time: Can test from 2019 onwards
"""

from maticalgos.historical import historical
import datetime
import pandas as pd
import quantstats as qs
import numpy as np

email = 'vama.patel@finideas.com'
password = 291410
ma = historical(email)
ma.login(password)


def cash_flow (entry_long, entry_short, exit_long, exit_short):
    
    #Cash Flow = Spread_Value@close - Debit
    
    #Net Debit (Investment)
    net_credit = (entry_short - entry_long * 2 ) * lot_size
    
    spread_value = (exit_short - exit_long * 2 ) * lot_size

    return net_credit - spread_value 


dates = ma.get_dates("nifty")
trades = pd.DataFrame()
trades_list = []
kpi = {}
kpi_list = []
kpis = pd.DataFrame()
pnl = 0
lot_size = 75
cashbal = 200000
marketvalue = 0

for i in dates[-756:]: 
  
    date = datetime.datetime.strptime(i, "%Y%m%d").date()
    df = ma.get_data("nifty", date)
    df['datetime'] = df['date'] + " " + df['time']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index(df['datetime'])
    df[['open', 'high', 'low', "close"]] = df[['open', 'high', 'low', "close"]].astype(float)
    spotdata = df[df['symbol'] == "NIFTY" ]
    exp = df.iloc[0]['symbol'][5:12]
    strangle = False
    
    for s in range(len(spotdata)): 
        currentcandle = spotdata.iloc[s]
        if currentcandle.name.time() == datetime.time(9,20)  and not strangle : 
          
            cst = currentcandle['open']
            cstc1 = int(round(cst/100, 0 )*100)
            cstc2 = int(round(cst/100, 0 )*100)+100
            opdata = {"CE1" : df[df['symbol'] == "NIFTY" + exp +str(cstc1)  + "CE"] , 
                      "CE2" : df[df['symbol'] == "NIFTY" + exp +str(cstc2)  + "CE"] }
            print("Placing Call Ratio Back Spread!", currentcandle.name.date())
            ce1_sellprice = opdata["CE1"].loc[currentcandle.name]
            ce2_buyprice = opdata["CE2"].loc[currentcandle.name]
            td = {
                "CE1" : {
                      "symbol" : ce1_sellprice['symbol'], 
                      "entrydate" : currentcandle.name.date(), 
                      "entrytime" :  f"{currentcandle.name.date()} {currentcandle.name.time()}", 
                      "qty" : 75, 
                      "entryprice" : ce1_sellprice["open"], 
                      "sl" : (ce1_sellprice["open"])*1.15,  
                      "pos" : True, 
                      "entryspot" : cst,
                      "entrystrike1": cstc1
                      },
                  "CE2" : {
                      "symbol" :  ce2_buyprice['symbol'], 
                      "entrydate" : currentcandle.name.date(), 
                      "entrytime" :  f"{currentcandle.name.date()} {currentcandle.name.time()}", 
                      "qty" : 150, 
                      "entryprice" : ce2_buyprice["open"], 
                      "sl" : (ce2_buyprice["open"])*1.15,  
                      "pos" : True, 
                      "entryspot" : cst,
                      "entrystrike2": cstc2
                      }
                }
            strangle = True
       
        if strangle : 
            for t in ['CE1', "CE2"] :
                '''if (opdata["CE"].loc[currentcandle.name]['high'] + opdata["PE"].loc[currentcandle.name]['high']) >= td[t]['sl'] and td[t]['pos'] : 
                    td[t]['buyprice'] = opdata[t].loc[currentcandle.name]['open']
                    td[t]['buytime'] = currentcandle.name.time()
                    td[t]['reason'] = "SL HIT"
                    td[t]['pnl'] = (td[t]['sellprice'] - td[t]['buyprice'])*td[t]['qty']
                    td[t]['pos'] = False   '''           
                    
                   
                if currentcandle.name.time() == datetime.time(15,00) and td[t]['pos']  : 
                    td[t]['exitprice'] = opdata[t].loc[currentcandle.name]['open']
                    td[t]['exittime'] =  f"{currentcandle.name.date()} {currentcandle.name.time()}"
                    td[t]['reason'] = "Time Up"
                    td[t]['exitspot'] = currentcandle['open']
                    td[t]['pos'] = False
                   
                    
            #Appending all the trades and calculating performance parameters        
            if not td['CE1']['pos'] and not td['CE2']['pos']:
                
                trades_list.append(pd.DataFrame.from_dict(td, orient='index'))
                trades = pd.concat(trades_list, ignore_index=True)  
                
                cashflow = cash_flow(
                    td['CE1']['entryprice'],
                    td['CE2']['entryprice'],
                    td['CE1']['exitprice'],
                    td['CE2']['exitprice'],
                    )
                cashbal = cashbal + cashflow
                nlv = cashbal + marketvalue
                
                kpi = {
                   "entrytime": [td['CE1']['entrytime']],
                   "cashflow": [cashflow],
                   "nlv": [nlv]
                }
                
                
                kpi_list.append(pd.DataFrame.from_dict(kpi))
                kpis = pd.concat(kpi_list, ignore_index=True) 
                     #trades = pd.DataFrame().from_dict(td, orient = 'index')
                strangle = False
               
kpis['entrytime'] = pd.to_datetime(kpis['entrytime'])
backtest = kpis.set_index('entrytime')
# Calculate percentage pnl relative to entry price for each trade
backtest['returns'] = backtest['nlv'].pct_change().fillna(0)              

# Try generating the report
qs.reports.html(backtest['returns'], title='Intraday: Call Ratio Back Spread ', output='i_crbs.html')
