# Public source preview

This repository contains experimental game/simulation source. The reachable Git history and source were reviewed for publication on 2026-10-29; no protected-data or credential blocker was identified. This is not a guarantee that every feature works or that the program is secure to deploy.

## Verification

Python syntax was checked without importing or running the game (15 current Python files). Gameplay, graphics, trained policies and dependency installation were not verified for this publication. Existing tests have not been run unless a separate validation section says otherwise.

## Runtime boundaries

Review status: `trusted_local_save_files_only`.

- evolife/io.py:115,125,130,135 pickle.loads untrusted file sections selected through --load.

Run network prototypes only on a trusted local machine/LAN. They have not been reviewed for Internet exposure. Load only your own trusted pickle/model checkpoints; such files can execute code. Keep generated saves, models, credentials and personal data outside Git.
