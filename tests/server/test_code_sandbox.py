import os
import pytest
from app.server.code_sandbox import RECIPES, run_code,check_answer

def test_typescript_uses_supported_node_stdin_mode():
    image, command = RECIPES['typescript']
    assert image == 'node:24-alpine'
    assert command == ['sh', '-c', 'cat > /work/main.ts && node --experimental-strip-types /work/main.ts']

def test_unsupported_never_executes():
    assert run_code('ruby','puts 4')['status']=='unsupported'
    assert check_answer('No code')[0]['status']=='unsupported'

@pytest.mark.skipif(os.getenv('AIRIS_TEST_DOCKER')!='1',reason='explicit Docker integration test')
@pytest.mark.parametrize('language,code',[
 ('python','print(4)'),
 ('javascript','console.log(4)'),
 ('typescript','const x: number=4; console.log(x)'),
 ('bash','echo 4'),
 ('sql','CREATE TABLE t(id INTEGER); INSERT INTO t VALUES (4);'),
 ('c','#include <stdio.h>\nint main(){puts("4");return 0;}'),
 ('cpp','#include <iostream>\nint main(){std::cout<<4;}'),
 ('csharp','System.Console.WriteLine(4);'),
])
def test_languages(language,code):
    result=run_code(language,code)
    assert result['status']=='passed',result

@pytest.mark.skipif(os.getenv('AIRIS_TEST_DOCKER')!='1',reason='explicit Docker integration test')
def test_timeout_and_host_write_protection():
    assert run_code('python','while True: pass',timeout=1)['status']=='timeout'
    assert run_code('python','open("/blocked", "w").write("x")')['status']=='failed'
    assert run_code('python','import os; assert "KKU_API_KEY" not in os.environ; print(os.getuid())')['status']=='passed'
