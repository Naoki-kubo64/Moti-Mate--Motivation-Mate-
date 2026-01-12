$ButlerUrl = "https://broth.itch.ovh/butler/windows-amd64/LATEST/archive/default"
$ButlerZip = "butler.zip"
$DescPath = "./butler_tools"

# 1. Download Butler if not exists
if (-not (Test-Path "$DescPath/butler.exe")) {
    Write-Host "Downloading Butler..."
    Invoke-WebRequest -Uri $ButlerUrl -OutFile $ButlerZip
    
    Write-Host "Extracting Butler..."
    Expand-Archive -Path $ButlerZip -DestinationPath $DescPath -Force
    Remove-Item $ButlerZip
}

# 2. Login (This will open browser if not logged in)
Write-Host "Logging in to itch.io..."
& "$DescPath/butler.exe" login

# 3. Push
$User = "solax615"
$Project = "moti-matemotivation-"
$Channel = "windows"
$Target = "$User/$Project`:$Channel"
$BuildDir = "dist"

Write-Host "Uploading to $Target..."
& "$DescPath/butler.exe" push $BuildDir $Target

Write-Host "Done!"
