import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional
import time
from threading import Thread
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from simulator.ideal_gas import IdealGasSystem
from simulator.wave import Wave2DSystem


app = FastAPI()

class SimulatorList(Enum):
    IDEAL_GAS_SYSTEM = 'ideal_gas_system'
    WAVE_2D_SYSTEM = 'wave_2d_system'

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(len(self.active_connections))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


class WSMessageHandler:

    def __init__(self, websocket):
        self._ws = websocket
        self._is_connected = True

    def start_message_receive_loop(self) -> None:
        # Thread(
        #     target=self.message_receive_loop
        # ).start()
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(self.message_receive_loop())
        # loop.close()
        # asyncio.get_event_loop().create_task(self.message_receive_loop())
        pass

    async def message_receive_loop(self) -> None:
        print('message_receive_loop')
        while self._is_connected:
            print('message_receive_loop loop')
            data = await self._ws.receive_text()
            # data = self._ws.receive_text()
            print(f'received message : {data}')
            if data == 'close':
                print('disconnecting')
                self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected


manager = ConnectionManager()
g_simulators = {}


@app.get("/")
async def get():
    return 'simulator ready'


@app.websocket("/simulate/{simulator}")
async def ws_simulate(
    websocket: WebSocket,
    simulator: SimulatorList,
    simulator_id: Optional[int] = None,
    min_dt: Optional[float] = 0.005,
    max_dt:Optional[float] = 0.1,
):
    print(f'simulator_id : {simulator_id}')
    global g_simulators
    await manager.connect(websocket)
    message_handler = WSMessageHandler(websocket)
    message_handler.start_message_receive_loop()
    try:
        if simulator == SimulatorList.IDEAL_GAS_SYSTEM:
            ig_simulator = IdealGasSystem(
                n_particles=100,
                xmin=-10, xmax=10, ymin=-10, ymax=10, zmin=-10, zmax=10,
            )
            target_simulator = g_simulators[id(ig_simulator)] = ig_simulator
        elif simulator == SimulatorList.WAVE_2D_SYSTEM:
            target_simulator = Wave2DSystem(
                n_grid_x=50,
                n_grid_z=50,
                dx=0.25,
                dz=0.25,
            )
            g_simulators[id(target_simulator)] = target_simulator
        prev_dt = cur_dt = datetime.now()
        while True:
            cur_dt = datetime.now()
            dt = (cur_dt - prev_dt).total_seconds()
            dt = min(max_dt, dt)
            # print(f'dt : {dt}')
            target_simulator.update(dt=dt)
            states = target_simulator.get_states()
            states['simulator_id'] = id(simulator)
            await websocket.send_json(states)
            msg_received = await websocket.receive_text()
            if msg_received == 'close':
                print('received close message')
                manager.disconnect(websocket)
                break
            # print(states['time'])
            prev_dt = cur_dt
            wait_time = min_dt-(datetime.now()-cur_dt).total_seconds()
            wait_time = max(0, wait_time)
            # time.sleep(wait_time)
            #print(len(manager.active_connections))
    except (WebSocketDisconnect, Exception) as e:
        print(e)
        manager.disconnect(websocket)
        # await manager.broadcast(f"Client #{client_id} left the chat")
        # websockets.exceptions.ConnectionClosedError
