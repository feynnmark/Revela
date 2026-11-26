param([switch]$Launch)
$ErrorActionPreference = 'Stop'
if (![Environment]::Is64BitOperatingSystem) { throw 'Este paquete requiere Windows de 64 bits en un equipo Intel o AMD.' }
$package = Join-Path $PSScriptRoot 'dist\Revela'
if (!(Test-Path -LiteralPath (Join-Path $package 'Revela.exe'))) { $package = $PSScriptRoot }
if (!(Test-Path -LiteralPath (Join-Path $package 'Revela.exe'))) { throw 'No se encuentra el paquete Revela.exe. Extrae el ZIP completo primero.' }
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Revela'))
$target = Join-Path $installRoot 'Revela.exe'
$running = @(Get-Process -Name Revela -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $target })
if ($running.Count -gt 0) { throw 'Cierra Revela antes de instalar o actualizar.' }
if ([IO.Path]::GetFullPath($package).TrimEnd('\') -ne $installRoot.TrimEnd('\')) {
    New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
    Get-ChildItem -LiteralPath $package -Force | Copy-Item -Destination $installRoot -Recurse -Force
}
$uninstallerSource = Join-Path $PSScriptRoot 'Uninstall.ps1'
$uninstallerTarget = Join-Path $installRoot 'Uninstall.ps1'
if ((Test-Path -LiteralPath $uninstallerSource) -and ([IO.Path]::GetFullPath($uninstallerSource) -ne [IO.Path]::GetFullPath($uninstallerTarget))) { Copy-Item -LiteralPath $uninstallerSource -Destination $uninstallerTarget -Force }
if (!(Test-Path -LiteralPath $uninstallerTarget)) { throw 'El paquete esta incompleto: falta Uninstall.ps1.' }
$shell = New-Object -ComObject WScript.Shell
$shortcutPaths = @(
    (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Revela.lnk'),
    (Join-Path ([Environment]::GetFolderPath('Programs')) 'Revela.lnk')
)
foreach ($shortcutPath in $shortcutPaths) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $target
    $shortcut.WorkingDirectory = $installRoot
    $shortcut.IconLocation = "$target,0"
    $shortcut.Description = 'Revela - Convierte RAW e imagenes por tandas'
    $shortcut.Save()
}
$registration = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Revela'
New-Item -Path $registration -Force | Out-Null
foreach ($property in @{
    DisplayName='Revela'; DisplayVersion=(Get-Item -LiteralPath $target).VersionInfo.ProductVersion; Publisher='Revela';
    InstallLocation=$installRoot; DisplayIcon="$target,0";
    UninstallString=('powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $uninstallerTarget)
}.GetEnumerator()) { New-ItemProperty -Path $registration -Name $property.Key -Value $property.Value -PropertyType String -Force | Out-Null }
New-ItemProperty -Path $registration -Name NoModify -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $registration -Name NoRepair -Value 1 -PropertyType DWord -Force | Out-Null
$size = [int]((Get-ChildItem -LiteralPath $installRoot -File -Recurse | Measure-Object Length -Sum).Sum / 1KB)
New-ItemProperty -Path $registration -Name EstimatedSize -Value $size -PropertyType DWord -Force | Out-Null
Write-Output "Revela instalada: $target"
Write-Output 'Accesos creados en el escritorio y el menu Inicio.'
if ($Launch) { Start-Process -FilePath $target -WorkingDirectory $installRoot }
