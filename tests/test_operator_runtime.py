import shutil
import subprocess
from pathlib import Path

import pytest


def test_frontend_voice_and_drag(tmp_path):
    root=Path(__file__).resolve().parents[1]
    tsc=root/"web/node_modules/.bin/tsc"
    if not tsc.exists() or not shutil.which("node"):
        pytest.skip("Frontend toolchain unavailable")
    subprocess.run([str(tsc),str(root/"web/src/operatorRuntime.ts"),"--target","es2022","--module","commonjs","--skipLibCheck","--outDir",str(tmp_path)],check=True,cwd=root)
    subprocess.run(["node","-e",r'''
const assert=require('node:assert/strict');
const {dragUpdate,LatestVoiceQueue}=require(process.argv[1]);
(async()=>{
 let previous={x:5,y:10};
 const update=dragUpdate(previous,{x:25,y:40});
 previous.x=25;previous.y=40;previous=null;
 assert.deepEqual(update({x:100,y:200}),{x:120,y:230});
 const accepted=[],calls=[],errors=[];let resolve;
 const queue=new LatestVoiceQueue(value=>{calls.push(value);return new Promise(r=>resolve=r)},text=>accepted.push(text),e=>errors.push(e));
 queue.submit('first',queue.invalidate());
 queue.submit('second',queue.invalidate());
 queue.submit('latest',queue.invalidate());
 assert.deepEqual(calls,['first']); // Capture continues; only one STT in flight.
 resolve('obsolete command');await new Promise(r=>setImmediate(r));
 assert.deepEqual(accepted,[]);
 assert.deepEqual(calls,['first','latest']);
 resolve('new command');await new Promise(r=>setImmediate(r));
 assert.deepEqual(accepted,['new command']);
 queue.submit('after model dispatch',queue.invalidate());
 assert.equal(calls.length,3); // Not blocked by model response.
 queue.close();resolve('after permission revoked');await new Promise(r=>setImmediate(r));
 assert.deepEqual(accepted,['new command']);assert.deepEqual(errors,[]);
})().catch(e=>{console.error(e);process.exit(1)})
''',str(tmp_path/"operatorRuntime.js")],check=True)
