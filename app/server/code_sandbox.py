"""Disposable Docker runs: no network, host mounts, privileges or inherited keys."""
import re
import shutil
import subprocess
import threading
import time
import uuid

RECIPES={
 'python':('python:3.12-alpine',['python','-']),
 'javascript':('node:24-alpine',['node','--input-type=module']),
 'typescript':('node:24-alpine',['node','--input-type=module-typescript']),
 'bash':('bash:5.2',['bash','-s']),
 'sql':('python:3.12-alpine',['python','-c','import sqlite3,sys; c=sqlite3.connect(":memory:"); c.executescript(sys.stdin.read()); print("SQLite script completed")']),
 'c':('gcc:14',['sh','-c','cat > /work/main.c && gcc /work/main.c -o /work/main && /work/main']),
 'cpp':('gcc:14',['sh','-c','cat > /work/main.cpp && g++ /work/main.cpp -o /work/main && /work/main']),
 'csharp':('mcr.microsoft.com/dotnet/sdk:8.0',['sh','-c','dotnet new console --no-restore >/dev/null && cat > Program.cs && dotnet restore --ignore-failed-sources >/dev/null && dotnet run --no-restore'])
}
ALIASES={'py':'python','js':'javascript','ts':'typescript','sh':'bash','shell':'bash','c++':'cpp','c#':'csharp','cs':'csharp'}
_slots=threading.BoundedSemaphore(2)

def run_code(language,code,cancel=None,timeout=20):
    if not _slots.acquire(timeout=5):return {'status':'unavailable','language':language,'output':'Sandbox กำลังทำงานเต็มจำนวน'}
    try:return _run_code(language,code,cancel,timeout)
    finally:_slots.release()

def _run_code(language,code,cancel=None,timeout=20):
    if cancel and cancel.is_set():return {'status':'cancelled','language':language,'output':'ยกเลิกแล้ว'}
    language=ALIASES.get(language.lower(),language.lower())
    if language not in RECIPES: return {'status':'unsupported','language':language,'output':'ภาษาไม่รองรับ'}
    if len(code.encode())>32000: return {'status':'unsupported','language':language,'output':'โค้ดเกิน 32 KB'}
    docker=shutil.which('docker')
    if not docker: return {'status':'unavailable','language':language,'output':'ยังไม่ได้ติดตั้ง Docker'}
    image,command=RECIPES[language];name='airis-check-'+uuid.uuid4().hex
    args=[docker,'run','--rm','--pull=never','--name',name,'--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
          '--pids-limit=64','--memory=512m','--memory-swap=512m','--cpus=1','--user=65534:65534','--workdir=/work',
          '--tmpfs=/work:rw,exec,nosuid,size=134217728,mode=1777','--tmpfs=/tmp:rw,nosuid,size=67108864,mode=1777',
          '--env=HOME=/work','--env=DOTNET_CLI_TELEMETRY_OPTOUT=1','--env=DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1','--log-driver=none','-i',image,*command]
    output=bytearray();overflow=threading.Event();proc=None
    try:
        proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        def read():
            while True:
                chunk=proc.stdout.read1(4096)
                if not chunk: break
                room=64000-len(output);output.extend(chunk[:room])
                if len(chunk)>room: overflow.set();break
        reader=threading.Thread(target=read,daemon=True);reader.start()
        def write():
            try:proc.stdin.write(code.encode());proc.stdin.close()
            except (BrokenPipeError,OSError):pass
        writer=threading.Thread(target=write,daemon=True);writer.start()
        deadline=time.monotonic()+timeout;reason=None
        while proc.poll() is None:
            if cancel and cancel.is_set():reason='cancelled';break
            if overflow.is_set():reason='output_limit';break
            if time.monotonic()>deadline:reason='timeout';break
            time.sleep(.05)
        if reason:proc.kill()
        proc.wait(timeout=3);reader.join(timeout=2);writer.join(timeout=2)
        status=reason or ('output_limit' if overflow.is_set() else 'passed' if proc.returncode==0 else 'unavailable' if proc.returncode==125 else 'failed')
        return {'status':status,'language':language,'output':output.decode(errors='replace'),'exitCode':proc.returncode,'image':image}
    finally:
        # Exact generated name, never other containers; removes tmpfs and any running descendants.
        subprocess.run([docker,'rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
        if proc:
            for pipe in (proc.stdin,proc.stdout):
                if pipe and not pipe.closed:pipe.close()

def check_answer(answer,cancel=None):
    blocks=re.findall(r'^```([^\n`]*)\n([\s\S]*?)^```\s*$',answer,re.MULTILINE)
    if not blocks:return [{'status':'unsupported','language':'none','output':'ไม่พบ fenced code block'}]
    if len(blocks)>4:return [{'status':'unsupported','language':'multiple','output':'จำกัด 4 code blocks ต่อคำตอบ'}]
    results=[]
    for language,code in blocks:
        if cancel and cancel.is_set():return [{'status':'cancelled','language':language,'output':'ยกเลิกแล้ว'}]
        results.append(run_code(language.strip(),code,cancel))
    return results
