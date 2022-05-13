import ccxt
import schedule
import config
import ta
import time
from datetime import datetime
import pandas as pd
from ta.volatility import BollingerBands
from ta.trend import CCIIndicator

#pd.set_option('display.max_rows', None)

Band0 = 100
Band1 = -100
in_possition = False


exchange = ccxt.binance({
    'apiKey': config.BINANCE_API_KEY,
    'secret': config.BINANCE_SECRET_KEY
})


def bb_cci_indicator(df):
    buy_signal = False
    # BB_indicator
    bb_ind = BollingerBands(df['close'], 46, 3)
    df['upper_band'] = bb_ind.bollinger_hband()
    df['lower_band'] = bb_ind.bollinger_lband()
    df['moving_average'] = bb_ind.bollinger_mavg()
    df['bb_signal_buy'] = bb_ind.bollinger_lband_indicator()
    df['bb_signal_sell'] = bb_ind.bollinger_hband_indicator()
    df['bb_ma_signal'] = 0
    for i in range(len(df)):
        if df['close'][i] >= df['moving_average'][i]:
            df['bb_ma_signal'][i] = 1
        else:
            df['bb_ma_signal'][i] = 0
    # CCI_indicator
    cci_ind = CCIIndicator(df['high'], df['low'], df['close'], 20)
    df['cci_indicator'] = cci_ind.cci()
    df['in_uptrend'] = 0
    for current in range(1, len(df.index)):
        previous = current - 1
        if df['cci_indicator'][current] > Band1 and df['bb_signal_sell'][current] == 1:
            df['in_uptrend'][current] = -1
        if df['cci_indicator'][current] < Band0 and df['bb_signal_buy'][current] == 1:
            buy_signal = True
        if buy_signal and df['bb_ma_signal'][current] == 1:
            df['in_uptrend'][current] = 1
            buy_signal = False

    return df


def check_buy_sell_signals(df):
    print("Checking for buy and sell")
    print(df.tail(5))
    global in_possition
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1
    if df['in_uptrend'][last_row_index] == -1:
        if in_possition:
            print("Sell!")
            in_possition = False
        else:
            print("Nothing to sell!")
    if df['in_uptrend'][last_row_index] == 1:
        if not in_possition:
            print("Buy!")
            in_possition = True
        else:
            print("You are already in possition")


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ETH/USDT', limit=100, timeframe='5m')
    df = pd.DataFrame(bars[:-1], columns=['timestamp',
                      'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], unit='ms') + pd.Timedelta('03:00:00')
    bb_cci_data = bb_cci_indicator(df)
    check_buy_sell_signals(bb_cci_data)
    # print(bb_cci_data)


schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
