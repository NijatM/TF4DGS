(async()=>{
const pause=ms=>new Promise(r=>setTimeout(r,ms));const paint=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
const base=azimuth;await pause(1000);const phases=[];
for(const mode of ['rgb','displacement','recent']){
 document.getElementById('mode').value=mode;document.getElementById('history').value=3;document.getElementById('maximum').value=mode==='displacement'?250:100;document.getElementById('trails').checked=mode!=='rgb';
 const visits=[];
 for(let k=0;k<=120;k++){
  const start=performance.now(),u=k/120;document.getElementById('time').value=Math.round(u*(frames.length-1));azimuth=base+45*Math.sin(2*Math.PI*u);
  const i=Number(document.getElementById('time').value);while(busy)await pause(10);await update();await paint();
  if(!document.getElementById('status').textContent.includes('Gaussian render'))throw Error('Gaussian browser render failed');
  document.getElementById('captureCaption').textContent=(mode==='rgb'?'Trained RGB':mode==='displacement'?'Displacement from first supported pose':'3-second fading motion activity')+' | elevated iPhone-side orbit '+(azimuth-base).toFixed(1)+' degrees | geometry uses supported poses only';
  visits.push({index:frames[i].index,time_s:frames[i].time_s,azimuth_deg:azimuth});await pause(Math.max(0,100-(performance.now()-start)));
 }
 phases.push({mode,history_s:3,source_samples:visits});await pause(800);
}
return {phases,camera_trajectory:'Raised iPhone-side center -> +45 -> center -> -45 -> center, one smooth camera arc per mode',timing:'Actual wall-clock browser playback; camera moves smoothly while only supported model poses are displayed',temporal_gaussian_color:false,metric_accuracy_verified:false};})()
