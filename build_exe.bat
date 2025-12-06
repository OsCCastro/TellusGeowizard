@echo off
REM ═══════════════════════════════════════════════════════════════════
REM Script de compilación para GeoWizard - Tellus Consultoría
REM ═══════════════════════════════════════════════════════════════════

echo.
echo ════════════════════════════════════════════════════════════════
echo   COMPILANDO GEOWIZARD V.1.0 (BETA) - TELLUS CONSULTORIA
echo ════════════════════════════════════════════════════════════════
echo.

REM Verificar que PyInstaller esté instalado
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller no está instalado.
    echo.
    echo Instalando PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo instalar PyInstaller.
        echo Por favor ejecute: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [1/4] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo [2/4] Creando archivo de especificación...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['main.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('icons', 'icons'^),
echo         ('leaflet', 'leaflet'^),
echo         ('map_base.html', '.'^),
echo         ('LICENSE', '.'^),
echo     ],
echo     hiddenimports=[
echo         'PySide6.QtCore',
echo         'PySide6.QtGui',
echo         'PySide6.QtWidgets',
echo         'PySide6.QtSvg',
echo         'PySide6.QtSvgWidgets',
echo         'PySide6.QtWebEngineWidgets',
echo         'PySide6.QtWebEngineCore',
echo         'PySide6.QtWebChannel',
echo         'pyproj',
echo         'fiona',
echo         'fiona._shim',
echo         'fiona.schema',
echo         'pyshp',
echo         'lxml',
echo         'lxml.etree',
echo         'xml.etree.ElementTree',
echo         'xml.dom.minidom',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     [],
echo     exclude_binaries=True,
echo     name='GeoWizard',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon='icons/tellus_logo.png',
echo ^)
echo.
echo coll = COLLECT(
echo     exe,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     name='GeoWizard',
echo ^)
) > geowizard_build.spec

echo [3/4] Compilando con PyInstaller...
echo Esto puede tardar varios minutos...
echo.
pyinstaller --clean geowizard_build.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilación falló.
    echo Revise los errores anteriores.
    pause
    exit /b 1
)

echo.
echo [4/4] Limpiando archivos temporales...
del geowizard_build.spec
if exist build rmdir /s /q build

echo.
echo ════════════════════════════════════════════════════════════════
echo   ¡COMPILACIÓN EXITOSA!
echo ════════════════════════════════════════════════════════════════
echo.
echo El ejecutable se encuentra en:
echo   %cd%\dist\GeoWizard\GeoWizard.exe
echo.
echo Para distribuir, comprima toda la carpeta:
echo   %cd%\dist\GeoWizard\
echo.
echo ════════════════════════════════════════════════════════════════
echo.
pause
