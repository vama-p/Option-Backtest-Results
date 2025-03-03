

# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 10:39:30 2024

@author: fcamv

This strategy is an intraday strategy
SCRIPT: Nifty
Entry: Bull Put Spread at 9:15
Exit: 15:15
Time: Can test from 2019 onwards
"""

from maticalgos.historical import historical
import datetime
import pandas as pd
import quantstats as qs

email = 'vama.patel@finideas.com'
password = 291410
ma = historical(email)
ma.login(password)


def cash_flow(entry_short, entry_long, exit_short, exit_long, lot_size=75):
    # Net Credit Received (Initial Premium)
    net_credit = (entry_short - entry_long) * lot_size
    
    # Closing Spread Value
    spread_value = (exit_short - exit_long) * lot_size

    # Profit or Loss
    return net_credit - spread_value



dates = ma.get_dates("nifty")
trades = pd.DataFrame()
trades_list = []
kpi = {}
kpi_list = []
kpis = pd.DataFrame()
pnl = 0
lot_size = 75
cashbal = 300000
marketvalue = 0

for i in dates[-750:]: 
  
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
            cstp1 = int(round(cst/100, 0 )*100)-100
            cstp2 = int(round(cst/100, 0 )*100)-150
            opdata = {"PE1" : df[df['symbol'] == "NIFTY" + exp +str(cstp1)  + "PE"] , 
                      "PE2" : df[df['symbol'] == "NIFTY" + exp +str(cstp2)  + "PE"] }
            for key in opdata.keys():
                opdata[key] = opdata[key].sort_index().ffill()
            print("Placing Bull Put Spread!", currentcandle.name.date())
            pe1_sellprice = opdata["PE1"].loc[currentcandle.name]
            pe2_buyprice = opdata["PE2"].loc[currentcandle.name]
            td = {
                "PE1" : {
                      "symbol" : pe1_sellprice['symbol'], 
                      "entrydate" : currentcandle.name.date(), 
                      "entrytime" :  f"{currentcandle.name.date()} {currentcandle.name.time()}", 
                      "qty" : 75, 
                      "entryprice" : pe1_sellprice["open"], 
                      "sl" : (pe1_sellprice["open"])*1.15,  
                      "pos" : True, 
                      "entryspot" : cst,
                      "entrystrike1": cstp1
                      },
                  "PE2" : {
                      "symbol" :  pe2_buyprice['symbol'], 
                      "entrydate" : currentcandle.name.date(), 
                      "entrytime" :  f"{currentcandle.name.date()} {currentcandle.name.time()}", 
                      "qty" : 75, 
                      "entryprice" : pe2_buyprice["open"], 
                      "sl" : (pe2_buyprice["open"])*1.15,  
                      "pos" : True, 
                      "entryspot" : cst,
                      "entrystrike2": cstp2
                      }
                }
            strangle = True
       
        if strangle : 
            for t in ['PE1', "PE2"] :
                '''if (opdata["CE"].loc[currentcandle.name]['high'] + opdata["PE"].loc[currentcandle.name]['high']) >= td[t]['sl'] and td[t]['pos'] : 
                    td[t]['buyprice'] = opdata[t].loc[currentcandle.name]['open']
                    td[t]['buytime'] = currentcandle.name.time()
                    td[t]['reason'] = "SL HIT"
                    td[t]['pnl'] = (td[t]['sellprice'] - td[t]['buyprice'])*td[t]['qty']
                    td[t]['pos'] = False   '''           
                    
                   
                if currentcandle.name.time() == datetime.time(15,00) and td[t]['pos']  : 
                    if currentcandle.name in opdata[t].index:
                        td[t]['exitprice'] = opdata[t].loc[currentcandle.name]['open']
                    else:
                        td[t]['exitprice'] = opdata[t]['open'].reindex([currentcandle.name], method='ffill').iloc[-1]
                    td[t]['exittime'] =  f"{currentcandle.name.date()} {currentcandle.name.time()}"
                    td[t]['reason'] = "Time Up"
                    td[t]['exitspot'] = currentcandle['open']
                    td[t]['pos'] = False
                   
                    
            #Appending all the trades and calculating performance parameters        
            if not td['PE1']['pos'] and not td['PE2']['pos']:
                
                trades_list.append(pd.DataFrame.from_dict(td, orient='index'))
                trades = pd.concat(trades_list, ignore_index=True)  
                
                cashflow = cash_flow(
                    td['PE1']['entryprice'],
                    td['PE2']['entryprice'],
                    td['PE1']['exitprice'],
                    td['PE2']['exitprice'],
                    )
                cashbal = cashbal + cashflow
                nlv = cashbal + marketvalue
                
                kpi = {
                   "entrytime": [td['PE1']['entrytime']],
                   "cashflow": [cashflow],
                   "nlv": [nlv]
                }
                
                
                kpi_list.append(pd.DataFrame.from_dict(kpi))
                kpis = pd.concat(kpi_list, ignore_index=True) 
                strangle = False
               
kpis['entrytime'] = pd.to_datetime(kpis['entrytime'])
backtest = kpis.set_index('entrytime')
# Calculate percentage pnl relative to entry price for each trade
backtest['returns'] = backtest['nlv'].pct_change().fillna(0)              
qs.reports.html(backtest['returns'], title='Intraday: Bull Put Spread ', output='i_bps.html')               

