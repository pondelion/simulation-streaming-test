import websocket
from threading import Thread
import time
import json

import numpy as np

class WebsocketClient():

    def __init__(self, host_addr):
        # websocket.enableTrace(True)

        self.ws = websocket.WebSocketApp(host_addr,
            on_message = self.on_message,
            on_error   = self.on_error,
            on_close   = self.on_close,
        )
        self.ws.on_open = self.on_open

    def on_message(self, ws, message):
        print("receive : {}".format(message))

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print(f'close : {close_msg}')

    def on_open(self, ws):
        print('on_open')
        self._running = True
        Thread(
            target=self.run
        ).start()

    def run(self):
        while self._running:
            time.sleep(4)
            self.ws.send('ws_client')
        self.ws.close()
        print("thread terminating...")

    def run_forever(self):
        self.ws.run_forever()


ws_client = WebsocketClient("ws://localhost:8000/wstest")
ws_client.run_forever()
