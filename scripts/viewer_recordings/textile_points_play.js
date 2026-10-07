(async()=>{
const pause=ms=>new Promise(r=>setTimeout(r,ms));const paint=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
const baseYaw=yaw;await pause(1000);const phases=[];
for(const mode of ['since_start','recent']){
 document.getElementById('mode').value=mode;document.getElementById('gmax').value=mode==='since_start'?0.025:0.025;document.getElementById('cmax').value=mode==='since_start'?0.35:1.0;
 const visits=[];
 for(let i=0;i<=29;i++){
  const start=performance.now();yaw=baseYaw+(Math.PI/4)*Math.sin(2*Math.PI*(i-0)/29);document.getElementById('scrub').value=i;await update();if(document.getElementById('error').textContent)throw Error(document.getElementById('error').textContent);
  const positions=state.points.filter(p=>p.status==='tracked'&&p.position).length;document.getElementById('captureCaption').textContent=(mode==='since_start'?'Reference comparison':'3-second fading activity')+' | '+positions+' supported positions | orbiting point maps; no gap interpolation';
  await paint();visits.push({index:i,time_s:state.time_s,supported_positions:positions});await pause(Math.max(0,220-(performance.now()-start)));
 }
 phases.push({mode,history_s:3,geometry_max:Number(document.getElementById('gmax').value),appearance_max:Number(document.getElementById('cmax').value),source_samples:visits,point_map_orbit_arc_deg:45});await pause(800);
}
return {phases,appearance:'Observed fixed-camera linear RGB change; not trained temporal Gaussian color or calibrated pigment change',geometry:'Observed point movement; not independently verified material strain',timing:'Actual browser wall-clock capture; source timestamps remain visible'};})()