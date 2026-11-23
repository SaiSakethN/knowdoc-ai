$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
if (-not (Test-Path -LiteralPath '.env')) { throw 'Run python scripts/init_local.py first.' }
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8000 is already in use. Preserve the existing listener; stop only an owned project process before starting another.' }
docker compose up -d db
if ($LASTEXITCODE -ne 0) { throw 'Docker startup failed. Start Docker Desktop first.' }
& '.venv/Scripts/alembic.exe' upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
$logRoot = Join-Path $repoRoot 'artifacts/logs'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
Start-Process -FilePath (Join-Path $repoRoot '.venv/Scripts/python.exe') -ArgumentList '-m','uvicorn','knowdoc.api:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'api.log') -RedirectStandardError (Join-Path $logRoot 'api-error.log')
Start-Process -FilePath (Join-Path $repoRoot '.venv/Scripts/python.exe') -ArgumentList '-m','knowdoc.worker' -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'worker.log') -RedirectStandardError (Join-Path $logRoot 'worker-error.log')
Write-Output 'Local app: http://127.0.0.1:8000/ (build apps/web first). Logs: artifacts/logs/'
