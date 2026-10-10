# Terminal Flood + Root Folder Audit — 2026-09-05

## Symptom
Terminals (`cmd.exe` console windows) kept opening continuously on the PC.

## Root cause
Gemini Code Assist ("Antigravity") stores its MCP servers in **4 separate config copies**:
- `C:\Users\Alejandro\.gemini\antigravity\mcp_config.json`  (active — had `gmp-code-assist` disabled)
- `C:\Users\Alejandro\.gemini\config\mcp_config.json`        (had it disabled)
- `C:\Users\Alejandro\.gemini\antigravity-ide\mcp_config.json`   (**ENABLED**)
- `C:\Users\Alejandro\.gemini\antigravity-backup\mcp_config.json` (**ENABLED**)

The two enabled copies launched `@googlemaps/code-assist-mcp@latest` via `npx`. On Windows each
launch spawns a `cmd.exe` console window (`cmd /d /s /c code-assist-mcp`). The servers were never
cleaned up → **53 leaked processes (25 cmd + 28 node)**, terminals popping constantly.

## Actions taken
1. Set `"disabled": true` on `gmp-code-assist` in `antigravity-ide` and `antigravity-backup`
   (now consistent with the active config).
2. Killed the 53 leaked `cmd`/`node` processes. **Remaining: 0.** No relaunch observed.
3. Redacted the plaintext Google API key (`X-Goog-Api-Key: AQ.Ab8…`) in all 4 config files
   → **ACTION REQUIRED: rotate this key in the Google Cloud console** (it may already be exposed on disk).
4. Repaired `Start_DanielaOS.vbs` startup shortcut: wrong path `aig\scripts\start_daniela_master.ps1`
   → correct `aig\scripts\deploy\start_daniela_master.ps1` (real file confirmed to exist).
5. Removed dead HKCU `Run` entry `aig-DanielaMCP` (pointed to a non-existent `_ACTIVE` path).
6. Disabled scheduled task `aig-GitGuard`.

## Not yet fixed (needs attention)
- 3 scheduled tasks could not be disabled ("Acceso denegado" / admin needed):
  `aig_Grand_Suite_Auto`, `aig_RAM_Cleaner_Hourly`, `aig_Weekly_Cleanup`.
  All point to the non-existent `_ACTIVE\Development\PROYECTOS\aig-MONOREPO\...` tree.
  They run hidden (no visible window) but fail silently. Disable them from an elevated PowerShell:
  `Disable-ScheduledTask -TaskName "aig_Grand_Suite_Auto"` (repeat for the other two).
- Other exposed secrets from earlier audit (`.env` files, METAMASK_PRIVATE_KEY, SafePal seed) remain
  on disk in plaintext — recommend moving to a secret manager and rotating the wallets.

## Unresolved (carried over)
- Decentraland parcel coordinates: no LAND/NFT found in any of the 4 wallets derived from the
  MetaMask vault (password `Danieli.8374`) and the SafePal seed. Parcel location still unknown.
