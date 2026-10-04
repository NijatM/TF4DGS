# TF4DGS workspace instructions

- Leave all Git commits and pushes to the user, including source-fork pushes.
  Provide VS Code PowerShell commands with suitable commit messages. Do not
  run `git commit` or `git push` unless the user explicitly changes this rule.
- GitHub repository/fork creation is also left to the user for the current
  setup. Follow `GIT_SETUP.md` for the agreed workflow.
- Preserve the working static installation. LichtFeld and vcpkg are pinned
  submodules under `.local/src`; do not reset edits or advance their revisions
  without a deliberate project change and recorded validation.
- Keep installers, compiled apps, builds, caches, logs, footage, training
  outputs, environments and machine-specific JSON snapshots excluded from
  Git. Retain the setup scripts, source patch, environment recipe and useful
  checkpoint summaries.
- Update `PROJECT_MEMORY.md` before a required restart and resume from its
  checkpoint. Never restart Windows automatically.
- The static baseline is installed. The 4D trainer and analysis viewer remain
  later phases; select their implementation before adding research packages.
