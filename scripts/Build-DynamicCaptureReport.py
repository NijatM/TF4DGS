"""Build a local visual evidence report from the chronological Markdown log."""
import argparse
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, ImageOps


def read_json(path):
    raw=Path(path).read_bytes()
    encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    return json.loads(raw.decode(encoding))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('documentation/dynamic_capture_001'))
    args=parser.parse_args();out=args.output
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for name in ['yogurt','textile']:
        source=Path('.local/workflows')/f'dynamic_{name}_001/audit'
        canvas=Image.new('RGB',(1440,850),'#171b22');draw=ImageDraw.Draw(canvas)
        for col,cid in enumerate(['dji','fuji','iphone']):
            draw.text((col*480+14,12),f'{name} | {cid} | diagnostic previews',font=font,fill='white')
            for row,sample in enumerate([1,5,9]):
                with Image.open(source/cid/f'sample_{sample:02d}.png') as image:
                    thumb=ImageOps.contain(image.convert('RGB'),(466,238))
                    canvas.paste(thumb,(col*480+(480-thumb.width)//2,48+row*266))
        canvas.save(out/f'{name}_preview.jpg',quality=94)
        shutil.copy2(source/'contact_sheet.jpg',out/f'{name}_full_contact_sheet.jpg')
    canvas=Image.new('RGB',(1440,850),'#171b22');draw=ImageDraw.Draw(canvas)
    for col,cid in enumerate(['dji','fuji','iphone']):
        draw.text((col*480+15,12),f'Yogurt first frame: {cid} | 30 markers',font=font,fill='white')
        with Image.open(Path('.local/workflows/dynamic_yogurt_001/audit')/f'{cid}_markers_first.jpg') as image:
            thumb=ImageOps.contain(image.convert('RGB'),(470,790))
            canvas.paste(thumb,(col*480+(480-thumb.width)//2,48))
    canvas.save(out/'first_markers.jpg',quality=94)
    rows=[]
    for line in (out/'README.md').read_text(encoding='utf-8').splitlines():
        if line.startswith('| ') and line[2:4].isdigit():
            parts=[x.strip() for x in line.strip('|').split('|')]
            if len(parts)==3:rows.append(parts)
    numbers=[int(row[0].split(maxsplit=1)[0]) for row in rows]
    if sorted(numbers)!=list(range(1,len(rows)+1)):
        raise ValueError('Chronological stage numbers must be unique and consecutive')
    stages=[]
    for title,status,detail in sorted(rows,key=lambda row:int(row[0].split(maxsplit=1)[0])):
        number=int(title.split(maxsplit=1)[0])
        card={'number':number,'title':title,'status':status,'detail':detail,'retrospective':True}
        if number==2:card['image']='yogurt_preview.jpg'
        if number==3:card['image']='textile_preview.jpg'
        if number==4:card['image']='first_markers.jpg'
        if number==21:card['image']='rectified_lid_matches.jpg'
        if number==22:card['details']=read_json('data/dynamic_yogurt_001/calibration/board_lid_refinement_01/summary.json')
        if number==24:card['details']=read_json('data/dynamic_textile_001/calibration/cameras_crop_adjusted/summary.json')
        if number==25:card['details']=read_json('outputs/dynamic_yogurt_001/rigid_tracking_01/summary.json')
        if number==27:card['image']='yogurt_mask_diagnostic.jpg'
        if number==28:card['image']='yogurt_pilot_02_comparison.jpg'
        if number==30:card['image']='yogurt_pilot_03_comparison.jpg'
        if number==31:card['image']='textile_stereo_attempt_01.jpg'
        if number==32:card['image']='textile_stereo_attempt_02.jpg'
        if number==33:card['image']='textile_stereo_diagnostic.jpg'
        if number==34:card['details']={k:v for k,v in read_json('outputs/dynamic_textile_001/material_tracking_04/summary.json').items() if k!='per_frame_supported_points'}
        if number==36:card['image']='36_live_gaussian_rgb.png'
        if number==37:card['image']='yogurt_pilot_04_comparison.jpg'
        if number==38:card['image']='38_live_gaussian_displacement_trails.png'
        if number==39:card['details']=read_json('.local/workflows/dynamic_setup/real_pixel_verification.json')
        if number==40:card['image']='40_live_point_appearance_geometry.png'
        if number==41:card['image']='41_live_point_appearance_geometry.png'
        if number==42:card['image']='42_live_cleaner_gaussian_rgb.png'
        if number==43:card['details']=read_json('.local/workflows/dynamic_setup/current_stage_validation.json')
        if number==44:card['details']=read_json('outputs/dynamic_yogurt_001/rigid_tracking_02/summary.json')
        if number==45:card['details']=read_json('outputs/dynamic_yogurt_001/rigid_tracking_03/summary.json')
        if number==47:card['details']=read_json('outputs/dynamic_yogurt_001/rigid_tracking_04/summary.json')
        if number==48:card['details']=read_json(out/'container_measurements.json')
        if number==49:
            card['image']='measured_rim_checks.jpg'
            summary=read_json('data/dynamic_yogurt_001/calibration/board_lid_refinement_02_measured/summary.json')
            card['details']={k:v for k,v in summary.items() if k!='cameras'}
            canvas=Image.new('RGB',(1440,740),'#171b22')
            for col,cid in enumerate(['fuji','iphone','dji']):
                with Image.open(Path('data/dynamic_yogurt_001/calibration/board_lid_refinement_02_measured')/f'{cid}_rim_check.jpg') as image:
                    thumb=ImageOps.contain(image.convert('RGB'),(470,720))
                    canvas.paste(thumb,(col*480+(480-thumb.width)//2,(740-thumb.height)//2))
            canvas.save(out/'measured_rim_checks.jpg',quality=94)
        if number==50:card['details']=read_json('data/dynamic_textile_001/calibration/cameras_crop_adjusted_02_measured/summary.json')
        if number==51:card['details']={'failure':'PowerShell ClientWebSocket.ReceiveAsync canceled after 15 seconds','recovery':'Bring report tab to foreground before paint-cycle waits; save screenshot manifest incrementally'}
        if number==52:card['details']={name:read_json(f'outputs/dynamic_yogurt_001/{name}/summary.json') for name in ['rigid_tracking_05_measured','rigid_tracking_06_measured']}
        if number==53:card['details']=read_json('outputs/dynamic_yogurt_001/rigid_tracking_07_tabletop/summary.json')
        if number==54:
            source=Path('outputs/dynamic_yogurt_001/gaussian_pilot_05_measured')
            shutil.copy2(source/'heldout_comparison.jpg',out/'yogurt_pilot_05_comparison.jpg')
            card['image']='yogurt_pilot_05_comparison.jpg'
            card['details']=read_json(source/'summary.json')
        if number==55:card['image']='yogurt_pilot_05_comparison.jpg'
        if number==56:
            source=Path('outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid')
            shutil.copy2(source/'heldout_comparison.jpg',out/'yogurt_pilot_06_comparison.jpg')
            card['image']='yogurt_pilot_06_comparison.jpg'
            card['details']=read_json(source/'summary.json')
        if number==57:
            source=Path('outputs/dynamic_yogurt_001/measured_comparison_01')
            shutil.copy2(source/'comparison.jpg',out/'measured_model_comparison.jpg')
            card['image']='measured_model_comparison.jpg'
            card['details']=read_json(source/'summary.json')
        if number==58:card['image']='58_live_measured_gaussian_rgb.png'
        if number==59:card['image']='59_live_measured_gaussian_activity.png'
        if number==60:card['details']=read_json('.local/workflows/dynamic_setup/measured_stage_validation.json')
        if number==61:card['details']={'registered_current_views':0,'scene_merged':False,'constraint':'Current capture only; do not use earlier static scenes','archive':'.local/workflows/dynamic_setup/abandoned_static_room_registration_01'}
        if number==62:card['image']='current_empty_views.jpg'
        if number==63:card['details']=read_json('.local/workflows/dynamic_setup/depth_model_download.json')
        if number==64:
            shutil.copy2('outputs/dynamic_yogurt_001/static_background_01/initialization_diagnostic.jpg',out/'background_01_failed_interval.jpg')
            card['image']='background_01_failed_interval.jpg'
        if number==65:
            shutil.copy2('outputs/dynamic_yogurt_001/static_background_02/initialization_diagnostic.jpg',out/'background_02_clean_interval.jpg')
            card['image']='background_02_clean_interval.jpg'
        if number==66:
            h=read_json('outputs/dynamic_yogurt_001/static_background_02/trained_01/history.json')
            card['details']={'initial':h[0],'last_training':h[-2],'selected':h[-1],'actual_export_points':370081,'selected_for_final_scene':False}
        if number==67:
            source=Path('outputs/dynamic_yogurt_001/static_background_02/trained_02')
            shutil.copy2(source/'input_fit_comparison.jpg',out/'background_02_conservative_fit.jpg')
            card['image']='background_02_conservative_fit.jpg';card['details']=read_json(source/'summary.json')
        if number==68:card['image']='68_live_current_scene_initial.png'
        if number==69:
            card['details']=read_json('outputs/dynamic_yogurt_001/static_background_03/initialization.json')
        if number==70:
            source=Path('outputs/dynamic_yogurt_001/static_background_03/trained_01')
            shutil.copy2(source/'input_fit_comparison.jpg',out/'background_03_clean_fit.jpg')
            card['image']='background_03_clean_fit.jpg';card['details']=read_json(source/'summary.json')
        if number==71:card['image']='71_live_current_scene_start.png'
        if number==72:card['image']='72_live_current_scene_end.png'
        if number==73:card['image']='73_live_current_scene_activity.png'
        if number==74:card['details']={'failed_check':'Static RGB unchanged outside color-difference mask','cause':'White actor pixels may equal white background RGB','correction':'Mask the calibrated projected Gaussian bounds plus a support margin'}
        if number==75:
            result=read_json('.local/workflows/dynamic_setup/current_scene_validation.json')
            card['details']={k:v for k,v in result.items() if k!='motion_observations'}
            shutil.copy2('outputs/dynamic_yogurt_001/static_background_03/current_scene_motion_check.jpg',out/'current_scene_motion_check.jpg')
            card['image']='current_scene_motion_check.jpg'
        if number==76:card['details']={'environment':'tf4dgs','error':'ModuleNotFoundError: No module named cv2','recovery':'Use the existing tf4dgs-dynamic OpenCV installation','dataset_output_created':False}
        if number==77:
            source=Path('outputs/dynamic_textile_001/material_tracking_05_measured')
            shutil.copy2(source/'initial_stereo_diagnostic.jpg',out/'textile_measured_stereo.jpg')
            card['image']='textile_measured_stereo.jpg'
            card['details']={k:v for k,v in read_json(source/'summary.json').items() if k!='per_frame_supported_points'}
        if number==78:
            source=Path('outputs/dynamic_textile_001/material_tracking_06_raft')
            shutil.copy2(source/'initial_stereo_diagnostic.jpg',out/'textile_raft_stereo.jpg')
            card['image']='textile_raft_stereo.jpg'
            card['details']={name:{k:v for k,v in read_json(Path('outputs/dynamic_textile_001')/name/'summary.json').items() if k!='per_frame_supported_points'} for name in ['material_tracking_05_measured','material_tracking_06_raft']}
        if number==79:
            card['details']={'initial_capture_frames':319,'initial_view':'Fixed iPhone camera','superseded_by':'User requested an elevated camera arc; initial PNG capture remains in ignored cache, not a final video'}
        if number==80:
            card['details']={'first_failure':'Encoder rejected a single out-of-order browser PNG paint event','maximum_reversal_s':0.005388975143432617,'second_and_third_failures':'Duration checks caught an extra 0.8-second EOF hold after the repeated final PNG; changing the input time base alone did not remove it','correction':'Stable ordering by paint timestamp; verified 1 ms PNG input time base; explicit output duration retains exactly one final hold. Raw frames and failed encodings stay in ignored cache','model_changed':False}
        if number in (81,82,83):
            name={81:'yogurt_gaussian_orbit',82:'yogurt_geometry_and_appearance',83:'textile_geometry_and_appearance'}[number]
            card['image']='videos/'+name+'.jpg'
            card['video']='videos/'+name+'.mp4'
            manifest=read_json(out/'videos'/f'{name}.capture.json')
            card['details']={k:manifest[k] for k in ['filename','duration_s','bytes','width','height','codec','crf','capture_frames','timing']}
        if number==84:
            card['details']=read_json(out/'videos/validation.json')
        if number==11:card['details']=json.loads(Path('.local/workflows/dynamic_setup/gpu_validation.json').read_text())
        if number==7:
            failure=read_json('.local/workflows/dynamic_setup/conda_create.json')
            card['details']={'exception':failure.get('exception_name'),'reason':failure.get('message','').split('To accept')[0]}
        if number==6:
            card['details']={name:json.loads((Path('data')/f'dynamic_{name}_001/calibration/marker_audit/summary.json').read_text()) for name in ['yogurt','textile']}
        stages.append(card)
    (out/'stages.json').write_text(json.dumps(stages,indent=2)+'\n',encoding='utf-8')
    page='''<!doctype html><html><head><meta charset="utf-8"><title>TF4DGS real capture processing</title><style>
body{margin:0;background:#121820;color:#eef2f7;font:18px Arial,sans-serif}main{max-width:1420px;margin:32px auto;padding:0 25px}header{display:flex;justify-content:space-between;align-items:center}h1{font-size:27px;margin:8px 0}h2{font-size:31px;margin:20px 0}p{line-height:1.5}select{font:17px Arial;padding:10px;background:#263341;color:white;border:1px solid #6e859c;border-radius:6px}article{margin-top:26px;padding:24px;background:#1c2633;border:1px solid #394d64;border-radius:10px}.badge{font-weight:bold;color:#80e1b4}.failed{color:#ffb095}video{display:block;max-width:100%;max-height:620px;margin:22px auto 0}img{display:block;max-width:100%;max-height:720px;margin:22px auto 0;border-radius:8px}pre{background:#10171f;padding:18px;font:15px Consolas,monospace;white-space:pre-wrap;max-height:590px;overflow:auto}.note{color:#b6c3d3;font-size:15px}a{color:#8ecaff}
</style></head><body><main><header><div><h1>Temporal Fields 4D Gaussian Splatting</h1><div class="note">Real recordings | 2026-10-07 | processing evidence</div></div><select id="stage"></select></header><article id="card"></article><p class="note">Browser report of preserved processing evidence. Early-stage screenshots are retrospective, not original terminal captures. Diagnostic previews are resized; source/training resolution is retained. A provisional rigid yogurt Gaussian pilot is trained; full non-rigid textile reconstruction remains unfinished.</p><a href="videos/index.html">Video recordings</a> | <a href="README.md">Full chronological record</a> ? <a href="http://127.0.0.1:8100/">Live Gaussian viewer</a> ? <a href="http://127.0.0.1:8096/">Observed feature maps</a></main><script>
const stages=__STAGES__;const menu=document.getElementById('stage');for(const item of stages){const option=document.createElement('option');option.value=item.number;option.textContent=item.title+' — '+item.status;menu.append(option)}function render(){const item=stages.find(x=>x.number===Number(menu.value));const card=document.getElementById('card');card.replaceChildren();const badge=document.createElement('div');badge.className='badge'+(item.status.includes('Failed')?' failed':'');badge.textContent=item.status;card.append(badge);const heading=document.createElement('h2');heading.textContent=item.title;card.append(heading);const detail=document.createElement('p');detail.textContent=item.detail;card.append(detail);if(item.image&&!item.video){const image=document.createElement('img');image.src=item.image;image.alt='Actual recording diagnostic';card.append(image)}if(item.video){const video=document.createElement("video");video.controls=true;video.preload="metadata";video.src=item.video;video.poster=item.image;card.append(video)}if(item.details){const pre=document.createElement('pre');pre.textContent=JSON.stringify(item.details,null,2);card.append(pre)}history.replaceState(null,'','?stage='+item.number)}menu.value=new URLSearchParams(location.search).get('stage')||1;menu.onchange=render;render();window.tf4dgsStages=stages;
</script></body></html>'''.replace('__STAGES__',json.dumps(stages))
    (out/'index.html').write_text(page,encoding='utf-8')
    print(f'Created chronological report with {len(stages)} stages and real recording diagnostics.')


if __name__=='__main__':
    main()
