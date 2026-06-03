import os
import time
import ccxt

# Simple trading bot using moving average crossover strategy
# Configure API credentials and trading parameters here.
API_KEY = os.getenv('EXCHANGE_API_KEY', 'YOUR_API_KEY')
API_SECRET = os.getenv('EXCHANGE_API_SECRET', 'YOUR_API_SECRET')
EXCHANGE_ID = 'binance'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
FAST_PERIOD = 9
SLOW_PERIOD = 21
TRADE_AMOUNT = 0.001  # in base currency


def create_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    exchange = exchange_class({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
    })
    return exchange


def fetch_ohlcv(exchange, symbol, timeframe, limit=100):
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)


def calculate_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def get_close_prices(ohlcv):
    return [candle[4] for candle in ohlcv]


def get_position(exchange, symbol):
    try:
        balance = exchange.fetch_free_balance()
        base = symbol.split('/')[0]
        return float(balance.get(base, 0)) > 0
    except Exception:
        return False


def place_order(exchange, symbol, side, amount):
    print(f"Placing {side} order for {amount} {symbol}")
    if side == 'buy':
        return exchange.create_market_buy_order(symbol, amount)
    return exchange.create_market_sell_order(symbol, amount)


def main():
    exchange = create_exchange()
    position_open = False

    while True:
        try:
            ohlcv = fetch_ohlcv(exchange, SYMBOL, TIMEFRAME, limit=SLOW_PERIOD + 10)
            closes = get_close_prices(ohlcv)
            fast_sma = calculate_sma(closes, FAST_PERIOD)
            slow_sma = calculate_sma(closes, SLOW_PERIOD)

            if fast_sma is None or slow_sma is None:
                print('Waiting for enough data...')
                time.sleep(60)
                continue

            print(f"Fast SMA: {fast_sma:.2f}, Slow SMA: {slow_sma:.2f}")

            current_position = get_position(exchange, SYMBOL)

            if fast_sma > slow_sma and not current_position:
                place_order(exchange, SYMBOL, 'buy', TRADE_AMOUNT)
                position_open = True
            elif fast_sma < slow_sma and current_position:
                place_order(exchange, SYMBOL, 'sell', TRADE_AMOUNT)
                position_open = False
            else:
                print('No trade signal.')

        except ccxt.NetworkError as e:
            print('Network error:', str(e))
        except ccxt.ExchangeError as e:
            print('Exchange error:', str(e))
        except Exception as e:
            print('Unexpected error:', str(e))

        time.sleep(60)


if __name__ == '__main__':
    main()
