param(
    [Parameter(Position = 0)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",

    [Parameter(Position = 1)]
    [ValidateSet("up", "down", "ps", "logs", "build", "restart", "check", "migrate")]
    [string]$Action = "up"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$composeFile = if ($Environment -eq "prod") { "docker-compose.prod.yml" } else { "docker-compose.dev.yml" }
$envFile = if ($Environment -eq "prod") { ".env.docker" } else { ".env.docker.dev" }
$exampleFile = if ($Environment -eq "prod") { ".env.docker.example" } else { ".env.docker.dev.example" }

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $exampleFile)) {
        throw "未找到环境变量文件 $envFile，也未找到示例文件 $exampleFile。"
    }

    Copy-Item $exampleFile $envFile
    Write-Host "已根据 $exampleFile 创建 $envFile，请按需修改后重新执行。"
}

$baseArgs = @("compose", "--env-file", $envFile, "-f", $composeFile)

switch ($Action) {
    "up" {
        & docker @baseArgs up -d --build
    }
    "down" {
        & docker @baseArgs down
    }
    "ps" {
        & docker @baseArgs ps
    }
    "logs" {
        & docker @baseArgs logs -f
    }
    "build" {
        & docker @baseArgs build
    }
    "restart" {
        & docker @baseArgs up -d --build --force-recreate
    }
    "check" {
        if ($Environment -ne "dev") {
            throw "check 仅支持开发环境，请使用 .\scripts\docker.ps1 dev check"
        }
        & docker @baseArgs --profile checks run --rm backend-check
    }
    "migrate" {
        $svc = if ($Environment -eq "prod") { "backend" } else { "backend-dev" }
        Write-Host "在 $svc 容器中执行数据库迁移..."
        & docker @baseArgs exec $svc python manage.py migrate --noinput
    }
}
