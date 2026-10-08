# Data folder structure

This folder keeps the active runtime state and configuration at the root, while moving legacy/temporary artifacts into dedicated subfolders.

## Active root

The following files are intentionally kept at the root because they are still referenced by the app and marketplace runtime:

- `agents_catalog.json`
- `marketplace_catalog.json`
- `aigestion_config.json`
- `plugins_catalog.json`
- `memory.json`
- `journal.json`
- `tasks.json`
- `trusted_devices.json`
- database files such as `aig.db`, `memory.db`, `daniela_multiuser.db`

## Organized subfolders

- `archive/`: historical backups, old message dumps, obsolete exports and migration leftovers
- `archive/messages/`: legacy chat/text dumps from prior message extraction flows
- `archive/data_migration/`: migration and diff artifacts
- `tools/`: utility scripts and maintenance helpers
- `exports/`: generated exports ready to share or archive
- `generated/`: derived content and cached outputs

## Rule

Add new runtime or operational state only under the most specific folder. Keep app-critical JSON and database files at the root unless there is a clear compatibility reason to move them.
