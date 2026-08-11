param(
    [string]$DestinationRoot,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $codexRoot = $env:CODEX_HOME
    }
    else {
        $profileRoot = [Environment]::GetFolderPath("UserProfile")
        $codexRoot = Join-Path $profileRoot ".codex"
    }
}
else {
    $codexRoot = $DestinationRoot
}

$skillSource = Join-Path $packageRoot "skills\build-textbook-learning-package"
$skillTarget = Join-Path $codexRoot "skills\build-textbook-learning-package"
$agentSource = Join-Path $packageRoot "agents"
$agentTarget = Join-Path $codexRoot "agents"
$agentFiles = @(Get-ChildItem -LiteralPath $agentSource -Filter "*.toml")

if (-not (Test-Path -LiteralPath $skillSource)) {
    throw "Skill source not found: $skillSource"
}

if ((Test-Path -LiteralPath $skillTarget) -and -not $Force) {
    throw "Skill already exists at $skillTarget. Re-run with -Force to replace it."
}

foreach ($agentFile in $agentFiles) {
    $existingAgent = Join-Path $agentTarget $agentFile.Name
    if ((Test-Path -LiteralPath $existingAgent) -and -not $Force) {
        throw "Agent already exists at $existingAgent. Re-run with -Force to replace it."
    }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $skillTarget) | Out-Null
New-Item -ItemType Directory -Force -Path $agentTarget | Out-Null

if (Test-Path -LiteralPath $skillTarget) {
    Remove-Item -LiteralPath $skillTarget -Recurse -Force
}
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse

foreach ($agentFile in $agentFiles) {
    $target = Join-Path $agentTarget $agentFile.Name
    Copy-Item -LiteralPath $agentFile.FullName -Destination $target -Force:$Force
}

Write-Host "Installed Skill: $skillTarget"
Write-Host "Installed agents: $agentTarget"
Write-Host "Restart Codex or start a new session so the new Skill and agents are discovered."
