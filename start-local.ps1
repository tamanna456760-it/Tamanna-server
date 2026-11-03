$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker is not installed. Install Docker Desktop first." }
docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose plugin is required." }
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host 'Created private .env' }
$envText = Get-Content .env -Raw
if ($envText -notmatch '(?m)^ORCHESTRATOR_TOKEN=.{32,}$') {
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$token = [Convert]::ToHexString($bytes).ToLowerInvariant()
if ($envText -match '(?m)^ORCHESTRATOR_TOKEN=.*$') { $envText = [regex]::Replace($envText, '(?m)^ORCHESTRATOR_TOKEN=.*$', "ORCHESTRATOR_TOKEN=$token") } else { $envText = $envText.TrimEnd() + [Environment]::NewLine + "ORCHESTRATOR_TOKEN=$token" + [Environment]::NewLine }
Set-Content -Path .env -Value $envText -NoNewline
Write-Host 'Generated private ORCHESTRATOR_TOKEN in .env'
}
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Docker Compose startup failed. Run docker compose logs --tail=150" }
docker compose ps
Write-Host "Website: http://127.0.0.1:3000"
Write-Host "API health: http://127.0.0.1:8000/health"
Write-Host "API readiness: http://127.0.0.1:8000/health/ready"
