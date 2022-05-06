import WebSocket from "isomorphic-ws";
import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import * as THREE from 'three';
import { ThreeObject } from '../../types/Three';
import { ObjectFactory as OF } from '../../utils/three/ObjectFactory';
import { SceneManager } from "../../utils/three/SceneManager";


let times: number[] = [];
let positions: number[][][] = [];
let posIdx: number = 0;
let sceneManager: SceneManager;
let ws: WebSocket|null = null;

export interface Props {
};

const SPHScene: React.FC<Props> = (props: Props) => {
  console.log('ThreeBaseScene')

  const width: number = 1000
  const height: number = 600

  const [container, setContainer] = React.useState<HTMLDivElement|null>(null);
  const [clock, setClock] = React.useState<THREE.Clock>(new THREE.Clock());
  const [nParticles, setNParticles] = React.useState<number>(500);

  // const [ws, setWs] = React.useState<WebSocket|null>(null);
  const [wsCnt, setWsCnt] = React.useState<number>(0);

  const createObjects = (nParticles: number): ThreeObject[] => {
    // const objs: ThreeObject[] = []
    const objs: ThreeObject[] = [...new Array(nParticles)].map((v, idx) => {
      return {
        tag: `test${idx}`,
        obj: OF.createSphere(
          idx*0.02, 0, 0,
          0.1,
          0.8,
          "#FF0000",
          THREE.FrontSide,
        ),
        objType: "sphere"
      }
    })
    // objs.push({
    //   tag: "bg",
    //   obj: OF.createBufferGeometryPlane(10, 50),
    //   objType: "buffer_geometry"
    // })
    return objs
  }

  const connectWs = () => {
    if (ws === null) {
      console.log(`connecting : ${wsCnt}`)
      console.log(ws)
      const socket = new WebSocket('ws://192.168.0.6:8000/simulate/sph_system?simulator_id=1000');
      // setWs(socket);
      ws = socket;
      socket.onmessage = (msg: any) => {
        console.log(msg.data["positions"]);
        const data: any = JSON.parse(msg.data);
        times.push(data["time"]);
        positions.push(data["positions"])
        socket.send("ok");
      };
      // setWsCnt(wsCnt+1);
    }
  }

  const closeWs = () => {
    ws?.send("close");
    ws?.close();
    // setWs(null);
    ws = null;
    positions = [];
    times = [];
  }

  useEffect(() => {
    console.log('useeffect')
    //resetAll();
    sceneManager = new SceneManager(
      width, height, container!, (cnt: number) => {}
    )
    sceneManager.setObjects(createObjects(nParticles));
  }, [container, clock])

  useEffect(() => {
    console.log('useeffect3')
    const loop = () => {
      const objects = sceneManager.getObjects();
      if (positions.length > posIdx) {
        for (let objIdx = 0; objIdx < nParticles; objIdx++) {
          // scene.children[objIdx].position.set(
            objects[objIdx].obj.position.set(
            positions[posIdx][objIdx][0], positions[posIdx][objIdx][1], positions[posIdx][objIdx][2]
          );
        }
        // setPosIdx(posIdx + 1);
        //posIdx = posIdx + 1;
        setTimeout(loop, 2000*(times[1]-times[0]))
        positions.shift();
        times.shift();
        // console.log(`${posIdx} : ${positions.length} : ${posIdx}`)
        // setWsCnt(times[0]);
      } else {
        setTimeout(loop, 10)
      }
      const bgObj: any = sceneManager.findThreeObj("bg");
      if (bgObj !== null) {
        // console.log(bgObj.obj.geometry.attributes.position.array);
        bgObj.obj.geometry.attributes.position.needsUpdate = true;
        const p = bgObj.obj.geometry.attributes.position.array;
        p[5002] = 5.0*Math.sin(0.01*sceneManager.getAnimationCount())
        // p[61] = 5.0
        // p[62] = 5.0
      }
    }
    loop()
  }, [])

  return (
    <div>
      <div
        style={{ width: width, height: height }}
        ref={(container) => { setContainer(container) }}
      />
      <div id='vr_button'/>
      <button onClick={closeWs}>close ws connection</button>
      <button onClick={() => {connectWs()}}>connect ws</button>
      {/* <button onClick={() => {recreateRenderer()}}>recreate renderer</button> */}
      {/* <button onClick={() => {ws?.send("close"); ws?.close(); setWs(null);}}>send close message</button> */}
      {times[posIdx]}
    </div>
  )
}

export default SPHScene;
