$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$outputRoot = (Resolve-Path -LiteralPath (Join-Path $taskRoot 'out')).Path
if (Get-CimInstance Win32_Process -Filter "Name = 'ePSXe.exe'") { throw 'Emulator is running; cleanup postponed.' }
$targets = @(
  @{ mode='ver_buki_riko'; version='v1'; stem='shibuki_riko'; sha='b0d27711e80de85d83e7764f49a8efc61250fd77a56b40bb5e64095e34089102' },
  @{ mode='ver_buki_riko'; version='v2'; stem='shibuki_riko'; sha='b856a351bfea9f7a0579386fc92a3432d31cf2c5b675bdf39a043d4dbbad7a49' },
  @{ mode='ver_rin_nana'; version='v1'; stem='rin_nana'; sha='6b2702b30f322f72c5be5c677d5638feac8a3cb4396f6d5b01d79ab1b4b3dfbe' },
  @{ mode='ver_rin_nana'; version='v2'; stem='rin_nana'; sha='e31f03112d89aa7ac12441e154cc194abd4e3e8437e222be12c8ad9fb74cedc3' }
)
$protected = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'protection_before.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$approved = @()
foreach ($target in $targets) {
  $relative = 'out/' + $target.mode + '/sprite_style_unification_20261107_' + $target.version
  $folder = (Resolve-Path -LiteralPath (Join-Path $taskRoot $relative)).Path
  if (-not $folder.StartsWith($outputRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Outside workspace outputs' }
  $pointer = Get-Content -LiteralPath (Join-Path $taskRoot ('projects/' + $target.mode + '/current_build.json')) -Raw -Encoding UTF8
  if ($pointer.Contains('sprite_style_unification_20261107_' + $target.version) -or $pointer.Contains($target.sha)) { throw 'Active build referenced' }
  foreach ($extension in @('.bin','.cue')) {
    $path = (Resolve-Path -LiteralPath (Join-Path $folder ($target.stem + $extension))).Path
    if ([IO.Path]::GetDirectoryName($path) -ne $folder) { throw 'Unexpected resolved target' }
    $item = Get-Item -LiteralPath $path
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked target refused' }
    $rel = $relative + '/' + $target.stem + $extension
    if ($protected.files.PSObject.Properties.Name -contains $rel) { throw 'Protected target' }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($extension -eq '.bin' -and ($hash -ne $target.sha -or $item.Length -ne 592217136)) { throw ('Retired BIN hash mismatch: ' + $path) }
    if ($extension -eq '.cue') {
      $cue = Get-Content -LiteralPath $path -Raw -Encoding ASCII
      if (-not $cue.Contains('FILE "' + $target.stem + '.bin" BINARY')) { throw 'Unexpected cue target' }
    }
    $approved += [pscustomobject]@{path=$path; relative=$rel; sha256=$hash; size=$item.Length}
  }
}
# All exact paths and hashes are preflighted before any deletion. No recursive operations.
$report = [ordered]@{ reason='Retired own trial v1/v2 discs superseded by validated v4; source art, plans and evidence retained'; files=$approved; bytes_released=($approved | Measure-Object size -Sum).Sum }
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'retired_trial_cleanup.json') -Encoding UTF8
foreach ($file in $approved) { Remove-Item -LiteralPath $file.path }
foreach ($target in $targets) {
  $folder = Join-Path $taskRoot ('out/' + $target.mode + '/sprite_style_unification_20261107_' + $target.version)
  'Retired trial BIN/CUE removed after validated v4. Manifest, source art and build plans retained. See work/sprite_style_unification_20261107/retired_trial_cleanup.json. Current review: ../sprite_style_unification_20261107_v4/.' | Add-Content -LiteralPath (Join-Path $folder 'REVIEW_STATUS.md') -Encoding UTF8
}
[pscustomobject]@{removed_files=$approved.Count; bytes_released=$report.bytes_released} | ConvertTo-Json
