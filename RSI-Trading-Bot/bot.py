import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *


CLIENT = Client(config.API_KEY, config.API_SECRET)

ETHUSDT_SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
XRPUSDT_SOCKET = "wss://stream.binance.com:9443/ws/xrpusdt@kline_1m"

# RSI
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

ETH_TRADE_SYMBOL = "ETHUSD"
ETH_TRADE_QUANTITY = 0.005

closes = []

in_a_position = False


def order(symbol, quantity, side, order_type=ORDER_TYPE_MARKET):
    try:
        print("Sending order...")
        order = CLIENT.create_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity
        )
        print(order)

    except Exception as e:
        return False

    return True


def on_open(ws):
    print("Opened connection \n")


def on_close(ws):
    print("Closed connection \n")


def on_message(ws, message):
    global closes
    print("\nReceived message: \n")
    # print(message)

    json_message = json.loads(message)
    pprint.pprint(json_message)
    print()

    candlestick = json_message["k"]
    is_candlestick_closed = candlestick["x"]  # returns True or False
    close_price = candlestick["c"]  # closing price of the candle

    if is_candlestick_closed:
        print(f"\nCandle closed at: {close_price} \n")
        closes.append(float(close_price))
        print(f"Closes: \n{closes}")

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("All RSIs calculated so far:")
            print(rsi)

            last_rsi = rsi[-1]
            print(f"The current RSI is: {last_rsi}")

            if last_rsi > RSI_OVERBOUGHT:
                if in_a_position:
                    print("RSI is overbought. Sell")

                    # binance sell order:
                    order_succeeded = order(
                        ETH_TRADE_SYMBOL,
                        ETH_TRADE_QUANTITY,
                        SIDE_SELL,
                        order_type=ORDER_TYPE_MARKET,
                    )

                    if order_succeeded:
                        in_a_position = False

                else:
                    print("Overbought, but not in a position. Nothing to do.")

            if last_rsi < RSI_OVERSOLD:
                if in_a_position:
                    print("Oversold, but already in a position. Nothing to do.")
                else:
                    print("RSI is oversold. Buy")

                    # binance buy order:
                    order_succeeded = order(
                        ETH_TRADE_SYMBOL,
                        ETH_TRADE_QUANTITY,
                        SIDE_BUY,
                        order_type=ORDER_TYPE_MARKET,
                    )

                    if order_succeeded:
                        in_a_position = True


ws = websocket.WebSocketApp(
    ETHUSDT_SOCKET, on_open=on_open, on_close=on_close, on_message=on_message
)
ws.run_forever()
