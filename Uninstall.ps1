$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Revela')).TrimEnd('\')
$actual = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
if ($actual -ne $expected) { throw 'El desinstalador solo se ejecuta desde la carpeta instalada de Revela.' }
$registration = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Revela'
$registered = (Get-ItemProperty -Path $registration -ErrorAction Stop).InstallLocation
if ([IO.Path]::GetFullPath($registered).TrimEnd('\') -ne $expected) { throw 'La ruta registrada no coincide. No se elimino ningun archivo.' }
if ([Windows.MessageBox]::Show('Se quitara Revela y sus accesos directos. Tus fotos, resultados y preferencias se conservaran.', 'Desinstalar Revela', 'YesNo', 'Question') -ne 'Yes') { exit }
$running = @(Get-Process -Name Revela -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $expected 'Revela.exe') })
if ($running.Count -gt 0) { [Windows.MessageBox]::Show('Cierra Revela y vuelve a ejecutar el desinstalador.', 'Revela') | Out-Null; exit 1 }
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('DesktopDirectory'), [Environment]::GetFolderPath('Programs'))) {
    $shortcut = Join-Path $folder 'Revela.lnk'
    if (Test-Path -LiteralPath $shortcut) {
        if ($shell.CreateShortcut($shortcut).TargetPath -eq (Join-Path $expected 'Revela.exe')) { Remove-Item -LiteralPath $shortcut -Force }
    }
}
# Both absolute paths were checked above against the single intended installation directory.
Remove-Item -LiteralPath $expected -Recurse -Force
Remove-Item -LiteralPath $registration -Recurse -Force
[Windows.MessageBox]::Show('Revela se ha desinstalado. Tus fotos y resultados siguen en sus carpetas.', 'Revela') | Out-Null
