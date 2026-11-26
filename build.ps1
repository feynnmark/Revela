param([switch]$Test, [switch]$Package)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $python)) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
        & $python -m pip install -r requirements-build.txt
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    }
    & $python tools\make_icon.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el icono.' }
    & $python tools\collect_licenses.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron recopilar las licencias.' }
    & $python tools\write_version.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar la version.' }
    if ($Test) { & $python -m unittest discover -s tests -v; if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas.' } }
    & $python -m PyInstaller --noconfirm Revela.spec
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el empaquetado.' }
    foreach ($file in @('Install.cmd','install.ps1','Uninstall.ps1','README.md','TESTING.md','THIRD_PARTY_NOTICES.md','LICENSE','VERSION')) { Copy-Item -LiteralPath $file -Destination 'dist\Revela' -Force }
    & $python tools\audit_public.py --package 'dist\Revela'
    if ($LASTEXITCODE -ne 0) { throw 'El paquete no paso la revision de publicacion.' }
    if ($Package) {
        $version = (Get-Content -LiteralPath 'VERSION' -Raw).Trim()
        $archive = Join-Path $PSScriptRoot ("dist\Revela-{0}-Windows-x64.zip" -f $version)
        Compress-Archive -LiteralPath 'dist\Revela' -DestinationPath $archive -Force
        $checksum = '{0}  {1}' -f (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant(), [IO.Path]::GetFileName($archive)
        [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'dist\SHA256SUMS.txt'), $checksum + "`n", [Text.UTF8Encoding]::new($false))
        Write-Output $checksum
    }
} finally { Pop-Location }
