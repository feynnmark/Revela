# Revela

<!-- impeccable:product-schema 1 -->

## Platform
web

Windows desktop application with a local WebView2 interface. The distributed package targets Windows 10/11 x64 on Intel and AMD computers.

## Users and purpose
Batch conversion of RAW photographs and common image files to JPG, WebP, PNG and TIFF. The workflow is to add files or folders, inspect a preview, choose export settings and convert.

## Operating context
Revela works with files from different camera and phone brands. No connected camera, device-specific driver, account or online service is required. Installation is per user and creates desktop and Start menu shortcuts. The interface is Spanish, dark and sober.

## Capabilities and constraints
Local processing, protected originals, collision-safe output names, proportional resizing, per-file errors and cancellation. Camera compatibility is determined by the bundled LibRaw decoder and the input format; no camera model is hardcoded as a requirement.

## Implementation decisions
Python, pywebview, rawpy and Pillow. Assets and fonts are bundled. No telemetry, image uploads or remote conversion backend.
