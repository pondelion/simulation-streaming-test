import asyncio
from datetime import datetime
from email.errors import MessageError
from enum import Enum
from typing import Optional, List
import time
from threading import Thread
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from simulator.ideal_gas import IdealGasSystem
from simulator.wave import Wave2DSystem
from simulator.sph import SPHSystem


app = FastAPI()

class SimulatorList(Enum):
    IDEAL_GAS_SYSTEM = 'ideal_gas_system'
    WAVE_2D_SYSTEM = 'wave_2d_system'
    SPH_SYSTEM = 'sph_system'

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

    def __init__(self, websocket, simulator, connection_manager, min_dt, max_dt):
        self._ws = websocket
        self._simulator = simulator
        self._connection_manager = connection_manager
        self._is_connected = True
        self._max_dt = max_dt
        self._min_dt = min_dt

    async def message_send_task(self) -> None:
        prev_dt = cur_dt = datetime.now()
        while self._is_connected:
            cur_dt = datetime.now()
            dt = (cur_dt - prev_dt).total_seconds()
            dt = min(self._max_dt, dt)
            # print(f'dt : {dt}')
            self._simulator.update(dt=dt)
            states = self._simulator.get_states()
            states['simulator_id'] = id(self._simulator)
            await self._ws.send_json(states)
            prev_dt = cur_dt
            wait_time = self._min_dt-(datetime.now()-cur_dt).total_seconds()
            wait_time = max(0, wait_time)
            await asyncio.sleep(wait_time)

    async def message_receive_task(self) -> None:
        while self._is_connected:
            msg_received = await self._ws.receive_text()
            print(f'received msg : {msg_received}')
            if msg_received == 'close':
                print('received close message')
                self._connection_manager.disconnect(self._ws)
                self._is_connected = False
                break

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
        elif simulator == SimulatorList.SPH_SYSTEM:
            target_simulator = SPHSystem(n_particles=500)
            g_simulators[id(target_simulator)] = target_simulator

        message_handler = WSMessageHandler(websocket, target_simulator, manager, min_dt, max_dt)

        L = await asyncio.gather(
            message_handler.message_send_task(),
            message_handler.message_receive_task(),
        )
    except (WebSocketDisconnect, Exception) as e:
        print(e)
        manager.disconnect(websocket)
        # await manager.broadcast(f"Client #{client_id} left the chat")
