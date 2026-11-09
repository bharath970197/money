$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/bharath970197/money.git"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClonePath = Join-Path $env:TEMP ("moneyflow-github-" + [guid]::NewGuid().ToString("N"))
Write-Host "Cloning $RepoUrl ..."
git clone $RepoUrl $ClonePath
if ($LASTEXITCODE -ne 0) { throw "Git clone failed. Check Git installation and GitHub authentication." }
Get-ChildItem -LiteralPath $ProjectRoot -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $ClonePath -Recurse -Force
}
Set-Location $ClonePath
git add -A
if ($LASTEXITCODE -ne 0) { throw "git add failed." }
git commit -m "Upload complete MoneyFlow Python project"
if ($LASTEXITCODE -ne 0) { Write-Host "No new changes to commit; attempting push." }
git push origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed. Sign in to GitHub and run this script again." }
Write-Host "Success: complete MoneyFlow project pushed to https://github.com/bharath970197/money"
