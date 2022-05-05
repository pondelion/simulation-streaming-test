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
const uniforms = {
  cnt:{type:'f',value:0.0}
};

export interface Props {
};

const Wave2DScene: React.FC<Props> = (props: Props) => {
  console.log('Wave2DScene')

  const width: number = 1000
  const height: number = 600

  const [container, setContainer] = React.useState<HTMLDivElement|null>(null);
  const [clock, setClock] = React.useState<THREE.Clock>(new THREE.Clock());
  const [nParticles, setNParticles] = React.useState<number>(100);

  // const [ws, setWs] = React.useState<WebSocket|null>(null);
  const [wsCnt, setWsCnt] = React.useState<number>(0);

  const createObjects = (nParticles: number): ThreeObject[] => {
    const objs: ThreeObject[] = []
    // const objs: ThreeObject[] = [...new Array(nParticles)].map((v, idx) => {
    //   return {
    //     tag: `test${idx}`,
    //     obj: OF.createSphere(
    //       idx*0.1, 0, 0,
    //       0.5,
    //       0.8,
    //       "#FF0000",
    //       THREE.FrontSide,
    //     ),
    //     objType: "sphere"
    //   }
    // })
    const bgObj = OF.createBufferGeometryPlane(10, 50);
    objs.push({
      tag: "bg",
      obj: bgObj,
      objType: "buffer_geometry"
    })
    console.log(bgObj.geometry.attributes.position.array.length)
    objs.push(getShaderObject2());
    return objs
  }

  const connectWs = () => {
    if (ws === null) {
      console.log(`connecting : ${wsCnt}`)
      console.log(ws)
      const socket = new WebSocket('ws://192.168.0.6:8000/simulate/wave_2d_system?simulator_id=1000');
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
      // const objects = sceneManager.getObjects();
      // if (positions.length > posIdx) {
      //   for (let objIdx = 0; objIdx < nParticles; objIdx++) {
      //     // scene.children[objIdx].position.set(
      //       objects[objIdx].obj.position.set(
      //       positions[posIdx][objIdx][0], positions[posIdx][objIdx][1], positions[posIdx][objIdx][2]
      //     );
      //   }
      //   setTimeout(loop, 2000*(times[1]-times[0]))
      //   positions.shift();
      //   times.shift();
      //   // console.log(`${posIdx} : ${positions.length} : ${posIdx}`)
      // } else {
      //   setTimeout(loop, 10)
      // }
      const bgObj: any = sceneManager.findThreeObj("bg");
      if (bgObj !== null) {
        // console.log(bgObj.obj.geometry.attributes.position.array);
        bgObj.obj.geometry.attributes.position.needsUpdate = true;
        const p = bgObj.obj.geometry.attributes.position.array;
        // for (let i = 0; i < Math.floor(p.length/3); ++i) {
        //   p[3*i+1] = 1.0*Math.sin(0.01*sceneManager.getAnimationCount()+0.02*i)
        // }
        // p[5002] = 5.0*Math.sin(0.01*sceneManager.getAnimationCount())
        // p[61] = 5.0
        // p[62] = 5.0

        if (positions.length > posIdx) {
          for (let vIdx = 0; vIdx < positions[posIdx].length; ++vIdx) {
            p[3*vIdx] = positions[posIdx][vIdx][0];
            p[3*vIdx+1] = positions[posIdx][vIdx][1];
            p[3*vIdx+2] = positions[posIdx][vIdx][2];
          }
          setTimeout(loop, 2000*(times[1]-times[0]))
          positions.shift();
          times.shift();
          // console.log(`${posIdx} : ${positions.length} : ${posIdx}`)
        } else {
          setTimeout(loop, 10)
        }

        bgObj.obj.geometry.computeVertexNormals();
      }
      const cnt = sceneManager.getAnimationCount();
      uniforms.cnt.value = cnt;

      const triangle: any = sceneManager.findThreeObj("shader_obj2");
      if (triangle !== null) {
        triangle!.obj.geometry.attributes.displacement.array[0] = 1.25 * Math.sin(cnt/50);
        triangle!.obj.geometry.attributes.displacement.array[4] = 1.25* Math.sin(cnt/60);
        triangle!.obj.geometry.attributes.displacement.array[6] = -1.25 * Math.sin(cnt/70);
        triangle!.obj.geometry.attributes.displacement.needsUpdate = true;

        triangle!.obj.geometry.computeVertexNormals();
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

export default Wave2DScene;

const getShaderObject1 = (): ThreeObject => {
  const vertexShader = `
    uniform float cnt;
    attribute vec3 color;
    varying vec3 vColor;
    void main(){
      vColor = color;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position+cos(cnt/50.0),1.0);
    }
  `;
  const fragmentShader = `
    uniform float cnt;
    varying vec3 vColor;
    void main(){
      float r = vColor.r + cos(cnt/50.0);
      float g = vColor.g + cos(cnt/60.0);
      float b = vColor.b + cos(cnt/70.0);
      gl_FragColor = vec4(r, g, b ,1.0);
    }
  `;
  const geometry = new THREE.PlaneGeometry(5,5,10,10);
  const material = new THREE.ShaderMaterial({
    uniforms: uniforms,
    vertexShader:vertexShader,
    fragmentShader:fragmentShader,
    side: THREE.DoubleSide,
  });
  const plane = new THREE.Mesh(geometry,material);
  return {
    tag: "shader_obj1",
    obj: plane,
    objType: "plane"
  }
}

const getShaderObject2 = (): ThreeObject => {
  const vertexShader = `
    uniform float cnt;
    attribute vec3 color;
    varying vec3 vColor;
    attribute vec3 displacement;
    void main(){
      vColor = color;
      vec3 vv = position + displacement;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(vv,1.0);
    }
  `;
  const fragmentShader = `
    uniform float cnt;
    varying vec3 vColor;
    void main(){
      float r = vColor.r + cos(cnt/50.0);
      float g = vColor.g + cos(cnt/60.0);
      float b = vColor.b + cos(cnt/70.0);
      gl_FragColor = vec4(r, g, b ,1.0);
    }
  `;
  const positions = new Float32Array([
    2.5,0.0,0.0,
    0,5.0,0.0,
    -2.5,0.0,0.0,
    ]);
  const colors = new Float32Array([
      1.0,0.0,0.0,
      0.0,0.0,1.0,
      0.0,1.0,0.0,
      ]);

  const displacement = new Float32Array(3*3);
  
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));

  geometry.setAttribute('displacement',new THREE.BufferAttribute(displacement,3));

  const material = new THREE.ShaderMaterial({
    vertexShader:vertexShader,
    fragmentShader:fragmentShader,

    uniforms:uniforms,
    side:THREE.DoubleSide,
  });
  const triangle = new THREE.Mesh(geometry,material);
  return {
    tag: "shader_obj2",
    obj: triangle,
    objType: "buffer_geometry"
  }
}