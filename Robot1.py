from binance.client import Client as binance_Client 
import datetime 
import time 
import pandas as pd 
import requests 
import json 
from line_notify import LineNotify 

#def robot1():
# 初始化LineNotify
lineToken = 'XwNODoIWQUsepXkwP6AvFFKYA8DhAASrDqt6O9td5qq'
notify = LineNotify(lineToken)

def fetch(FilePath,PairName,Interval):

    dataset = pd.DataFrame(columns=['Time','OpenPrice','HighPrice','LowPrice','ClosePrice'])
    try:
        #參數設置
        Payload = {
            'symbol':PairName,
            'interval':Interval,
            'limit':61
        }

        r = requests.get('https://fapi.binance.com/fapi/v1/klines',params=Payload)
        jsonResult = json.loads(r.text)
        if str(jsonResult) == "{'code':-1023,'msg':'Start time is greater than end time.'}" or len(jsonResult)==1:
            print('Error')
        
        # 對於每根k棒，拿出我們想要的數據然後依序放入dataframe裡
        for kline in jsonResult:
            TimeStamp = int(kline[0]/1000)
            StructTime = time.localtime(TimeStamp)
            TimeString = time.strftime('%Y-%m-%d %H:%M:%S',StructTime)
            OpenPrice = kline[1] 
            HighPrice = kline[2] 
            LowPrice = kline[3] 
            ClosePrice = kline[4] 

            test = pd.DataFrame(
                {'Time':[TimeString],
                'OpenPrice':[OpenPrice],
                'HighPrice':[HighPrice],
                'LowPrice':[LowPrice],
                'ClosePrice':[ClosePrice],}
            )

            dataset = pd.concat([dataset,test],axis=0)
        
    except:
        print('休息1秒後再對幣安發動請求')
        time.sleep(1)
    
    dataset.to_csv(FilePath+".csv",index=False)
    print("幣對: " +(PairName)+"爬取已完成")
    dataset = pd.read_csv("./try.csv")
    return dataset

def ordersignal(data):

    signal = 0 # 1表示買進 -1表示賣出 0表示什麼都不做

    #計算移動平均和收盤價
    ma5 = data['ClosePrice'].iloc[-6:-1].mean() 
    ma10 = data['ClosePrice'].iloc[-11:-1].mean() 
    ma20 = data['ClosePrice'].iloc[-21:-1].mean()
    ma40 = data['ClosePrice'].iloc[-41:-1].mean()
    ma60 = data['ClosePrice'].iloc[-61:-1].mean()
    dataclose = data['ClosePrice'].iloc[-2]

    # 多頭排列
    long_arrangement = (ma5>ma10 and ma10>ma20 and ma20>ma40 and ma40>ma60)
    # 收盤價下穿ma10
    crossdown = data['ClosePrice'].iloc[58] > data['ClosePrice'].iloc[0:60].tail(10).mean() and dataclose<ma10 
    # ma5下穿ma20
    long_exit = (ma5 < ma20 and data['ClosePrice'].iloc[0:59].tail(5).mean() > data['ClosePrice'].iloc[0:59].tail(20).mean())

    # 進出場訊號
    enter_condition = long_arrangement and crossdown 
    exit_condition = long_exit 

    if enter_condition:
        signal = 1 
    
    if exit_condition:
        signal = -1 
    
    return signal 

def run():

    # API key 
    A_api_key = "x4i3KrfjXVqMG7wEYNKhaVnPIjhH22n9J4dbwDqo8g7u1wGeBFaWQQgmfMxU36KZ"
    A_api_sec = "1mpHARmDa5jcsUTRTWzJxOYtgY43AtABQwnjoNc9avNsphleZhcg1MJcM9t5igsP"

    # 實體化
    A_Client = binance_Client(A_api_key,A_api_sec)

    # 下單數量
    order_q = 0.001 

    # 倉位紀錄
    marketposition = 0

    # 持續判斷
    while True:
        # 每過1個小時判斷一次是否需要進場
        print('Run......')

        # 判斷是否進場
        dataset = fetch('try','BTCUSDT','1h')

        strategy_name = '多頭回踩策略'
        close = '最新收盤價：' + str(dataset['ClosePrice'].iloc[59])
        ma5 = 'ma5:' + str(dataset['ClosePrice'].iloc[0:60].tail(5).mean())
        ma10 = 'ma10: ' + str(dataset['ClosePrice'].iloc[0:60].tail(10).mean())
        ma20 = 'ma20: ' + str(dataset['ClosePrice'].iloc[0:60].tail(20).mean())
        ma40 = 'ma40: ' + str(dataset['ClosePrice'].iloc[0:60].tail(40).mean())
        ma60 = 'ma60: ' + str(dataset['ClosePrice'].iloc[0:60].mean())
        signal = ordersignal(dataset)
        command = '' 
        if signal==1 and marketposition==0:
            command = '買入'
        elif signal==-1 and marketposition==1:
            command = '賣出'
        else:
            command = '不動作'
        
        msg = strategy_name+'\n'+close+'\n'+ma5+'\n'+ma10+'\n'+ma20+'\n'+ma40+'\n'+ma60+'\n'+command
        # send message 
        notify.send(msg)

        if ordersignal(dataset)==1 and marketposition==0:
            print('現在時間:',datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S"))
            # 市價單
            A_Client.futures_create_order(symbol='BTCUSDT',side='BUY',type='MARKET',quantity=order_q)
            print('Successfully placing order!')
            # 更新倉位
            marketposition = 1
        
        elif ordersignal(dataset)==-1 and marketposition==1:
            print('現在時間: ',datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S"))
            # 市價單
            A_Client.futures_create_order(symbol='BTCUSDT',side='SELL',type='MARKET',quantity=order_q,reduceOnly='true')
            print('Successfully Closed Position!')
            # 更新倉位
            marketposition = 0 
        
        else:
            pass 
        
        print('Robot1 Done'+'\n')

        time.sleep(3600)



        




