import WebSocket from "isomorphic-ws";
import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import * as THREE from 'three';
import { ThreeObject } from '../../types/Three';
import { OrbitControls } from '../../utils/three/OrbitControls';
import { VRButton } from '../../utils/three/VRButton';
import { ObjectFactory as OF } from '../../utils/three/ObjectFactory';


let times: number[] = [];
let positions: number[][][] = [];
let posIdx: number = 0;
let renderer: THREE.WebGLRenderer = new THREE.WebGLRenderer({ antialias: true })
let scene: THREE.Scene = new THREE.Scene();
let objects: ThreeObject[] = [];

export interface Props {
};

const IdealGasScene: React.FC<Props> = (props: Props) => {
  console.log('ThreeBaseScene')

  const _lookAt = new THREE.Vector3(0, 0, 0);
  const width: number = 1000
  const height: number = 600

  const [container, setContainer] = React.useState<HTMLDivElement|null>(null);
  // const [scene, setScene] = React.useState<THREE.Scene>(new THREE.Scene());
  const [camera, setCamera] = React.useState<THREE.PerspectiveCamera>(
    new THREE.PerspectiveCamera(
      45,
      width / height,
      0.1,
      1000
    )
  );
  const [lookAt, setLookAt] = React.useState<THREE.Vector3>(_lookAt);
  // const [renderer, setRenderer] = React.useState<THREE.WebGLRenderer>(new THREE.WebGLRenderer({ antialias: true }));
  const [bgColor, setBgColor] = React.useState<THREE.Color>(new THREE.Color('#b4bad2'));
  const [clock, setClock] = React.useState<THREE.Clock>(new THREE.Clock());
  const [cnt, setCnt] = React.useState<number>(0);
  const [orbitControls, setOrbitControls] = React.useState<OrbitControls|null>(null);
  // const [objects, setObjects] = React.useState<ThreeObject[]>([]);
  const [nParticles, setNParticles] = React.useState<number>(100);

  const [ws, setWs] = React.useState<WebSocket|null>(null);
  const [wsCnt, setWsCnt] = React.useState<number>(0);
  // const [times, setTimes] = React.useState<number[]>([]);
  // const [positions, setPositions] = React.useState<number[][]>([]);
  // const [posIdx, setPosIdx] = React.useState<number>(0);

  // contextValue.camera.position.x = contextValue.camera.position.x;
  // contextValue.camera.position.y = contextValue.camera.position.y;
  // contextValue.camera.position.z = contextValue.camera.position.z;
  // camera.position.set(5, 5, 5);
  // camera.lookAt(new THREE.Vector3(lookAt.x, lookAt.y, lookAt.z));
  // // setCamera(camera); NG

  // renderer!.setSize(width, height);
  // renderer!.setClearColor(bgColor);
  // renderer!.shadowMap.enabled = true;
  // renderer!.xr.enabled = true;

  const createObjects = (nParticles: number): ThreeObject[] => {
    const objs: ThreeObject[] = [...new Array(nParticles)].map((v, idx) => {
      return {
        tag: `test${idx}`,
        obj: OF.createSphere(
          idx*0.1, 0, 0,
          0.5,
          0.8,
          "#FF0000",
          THREE.FrontSide,
        ),
        objType: "sphere"
      }
    })
    return objs
  }

  const resetObjects = (): void => {
    // Reset objects
    scene.remove.apply(scene, scene.children);
    const objs = createObjects(nParticles);
    // setObjects(objs);
    objects = objs;
    objs.map(obj => scene.add(obj.obj));

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const spotLight = new THREE.SpotLight(0xffffff, 2.0, 100, Math.PI / 4, 1);
    spotLight.position.set(2, 7, 2);
    spotLight.castShadow = true;
    scene.add(spotLight);

    console.log(scene)
  }

  const resetAll = () => {
    camera.position.set(5, 5, 5);
    camera.lookAt(new THREE.Vector3(lookAt.x, lookAt.y, lookAt.z));

    renderer!.setSize(width, height);
    renderer!.setClearColor(bgColor);
    renderer!.shadowMap.enabled = true;
    renderer!.xr.enabled = true;

    // recreateRenderer();
    if (container) {
      if (container.childNodes.length === 0) {
        container.appendChild(renderer!.domElement);
      }
      console.log(container);
      const _orbitControls = new OrbitControls(camera, container);
      _orbitControls.target.set(0, 0, 0);
      _orbitControls.update();
      setOrbitControls(_orbitControls);
    }
    renderer!.setAnimationLoop(() => {
      setCnt(cnt+1);
      // update(clock.getDelta());
      renderer!.render(scene, camera);
    })
    ReactDOM.render(<div id='vr_button'/>, document.body.appendChild(VRButton.createButton( renderer )));

    resetObjects();
  }

  const recreateRenderer = () => {
    renderer.dispose();
    renderer.forceContextLoss();
    // renderer.context = null as any;
    // renderer.domElement = null as any;
    // setRenderer(new THREE.WebGLRenderer({ antialias: true }));
    renderer = new THREE.WebGLRenderer({ antialias: true });
  }

  // useEffect(() => {
  //   if (ws === null && wsCnt === 0) {
  //     console.log(`connecting : ${wsCnt}`)
  //     console.log(ws)
  //     const socket = new WebSocket('ws://192.168.0.6:8000/simulate/ideal_gas_system');
  //     setWs(socket);
  //     socket.onmessage = (data: any) => {
  //       console.log(data.data["positions"]);
  //     };
  //     setWsCnt(wsCnt+1);
  //   }
  // }, [ws, wsCnt]);

  const connectWs = () => {
    if (ws === null) {
      console.log(`connecting : ${wsCnt}`)
      console.log(ws)
      const socket = new WebSocket('ws://192.168.0.6:8000/simulate/ideal_gas_system');
      setWs(socket);
      socket.onmessage = (msg: any) => {
        // console.log(msg.data["positions"]);
        const data: any = JSON.parse(msg.data);
        // objects[0].obj.position.set(
        // scene.children[0].position.set(
        //   data["positions"][0][0], data["positions"][0][1], data["positions"][0][2]
        // );
        // console.log(data["time"])
        // console.log(objects[0].obj.position)
        // console.log(scene)
        // const posConcat = positions.concat(data["positions"])
        // const timesConcat = times.concat(data["times"])
        // setPositions(posConcat);
        // setTimes(timesConcat)
        times.push(data["time"]);
        positions.push(data["positions"])
        socket.send("ok");
      };
      setWsCnt(wsCnt+1);
    }
  }

  const closeWs = () => {
    ws?.send("close");
    ws?.close();
    setWs(null);
  }

  useEffect(() => {
    console.log('useeffect')
    // recreateRenderer();
    resetAll();
  }, [container, clock, renderer, scene, camera])

  useEffect(() => {
    console.log('useeffect3')
    // const moveObj = () => {
    //   scene.children[0].position.set(
    //     positions[1][0], positions[1][1], positions[1][2]
    //   );
    //   positions.shift();
    //   times.shift();
    //   setPositions(positions);
    //   setTimes(times);
    // }
    const loop = () => {
      // if (times.length >= 2) {
      //   setTimeout(moveObj, 1000*(times[1]-times[0]))
      // }
      if (positions.length > posIdx) {
        for (let objIdx = 0; objIdx < nParticles; objIdx++) {
          // scene.children[objIdx].position.set(
            objects[objIdx].obj.position.set(
            positions[posIdx][objIdx][0], positions[posIdx][objIdx][1], positions[posIdx][objIdx][2]
          );
        }
        // setPosIdx(posIdx + 1);
        //posIdx = posIdx + 1;
        setTimeout(loop, 2200*(times[1]-times[0]))
        positions.shift();
        times.shift();
        // console.log(`${posIdx} : ${positions.length} : ${posIdx}`)
        // setWsCnt(times[0]);
      } else {
        setTimeout(loop, 10)
      }
    }
    loop()
  }, [])

  // useEffect(() => {
  //   console.log('useeffect2')
  //   onReset();
  // }, [nParticles])

  return (
    <div>
      <div
        style={{ width: width, height: height }}
        ref={(container) => { setContainer(container) }}
      />
      <div id='vr_button'/>
      <button onClick={closeWs}>close ws connection</button>
      <button onClick={() => {resetAll(); connectWs()}}>connect ws</button>
      <button onClick={() => {recreateRenderer()}}>recreate renderer</button>
      <button onClick={() => {ws?.send("close"); ws?.close(); setWs(null);}}>send close message</button>
      {times[posIdx]}
    </div>
  )
}

export default IdealGasScene;
