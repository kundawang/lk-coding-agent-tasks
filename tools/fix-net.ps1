# 代理突然连不上 GitHub 时跑一下：清掉 Clash Verge 的 fake-ip 缓存 + Windows DNS 缓存。
# 现象是 curl/git 报 "schannel: failed to receive handshake"，节点其实是好的。
$ErrorActionPreference = "SilentlyContinue"

ipconfig /flushdns | Out-Null

$env:PYTHONIOENCODING = "utf-8"
uv run python -c @"
PIPE = r'\\.\pipe\verge-mihomo'
try:
    f = open(PIPE, 'r+b', buffering=0)
    f.write(b'POST /cache/fakeip/flush HTTP/1.1\r\nHost: localhost\r\nAuthorization: Bearer set-your-secret\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
    buf = b''
    while True:
        c = f.read(65536)
        if not c:
            break
        buf += c
    f.close()
    print('fakeip flush:', buf.split(b'\r\n')[0].decode())
except Exception as exc:
    print('fakeip flush 失败（代理没开就算了）:', exc)
"@

Start-Sleep -Seconds 2
curl.exe --ssl-no-revoke -sS -o NUL -w "github api: %{http_code}`n" --max-time 20 "https://api.github.com/rate_limit"
