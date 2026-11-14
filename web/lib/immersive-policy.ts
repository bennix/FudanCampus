import {Quaternion} from 'three';

export const observationPoints={
 teaching4:{name:'第四教学楼',position:[-154.4,0,-169] as [number,number,number],target:[-154.4,10,-204] as [number,number,number],eyeHeight:1.65},
 chemistry:{name:'化学楼',position:[-97.6,0,-119] as [number,number,number],target:[-97.6,6,-154] as [number,number,number],eyeHeight:1.65},
};
export type ObservationKey=keyof typeof observationPoints;
/** Desktop simulation only. Real XR poses must not be delayed with this filter. */
export function smoothHead(current:Quaternion,target:Quaternion,dt:number){
 current.slerp(target,1-Math.exp(-12*Math.max(0,dt)));
}
export function shouldRenderFrame(xr:boolean,experiment:boolean,dirty:boolean,elapsedMs:number,hz:number){
 return xr||experiment||(dirty&&elapsedMs>=1000/hz);
}
