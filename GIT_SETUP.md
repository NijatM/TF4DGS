# TF4DGS: Git setup and first push

GitHub account: `NijatM`. The main repository is private `NijatM/TF4DGS`;
the source fork is `NijatM/LichtFeld-Studio`.

Current checkpoint (2026-10-03): initial publication is complete. The user
created both repositories, published the packaging fix on the fork's `tf4dgs`
branch at `b4e26dc929d23ad8c4cc266e61eb8bf7334ede36`, and pushed TF4DGS's initial
commit `8e826bd113158a71ed8ab3d15e31335572ed91be` to `origin/main`.
TF4DGS records the fork URL and the tested vcpkg reference. Sections 1-3 document
the completed initial setup; use Section 4 when cloning on another machine.

The local repository has already been initialized with `git init -b main`.
The existing LichtFeld and vcpkg checkouts are registered as submodules at their
tested revisions. The local `main` branch tracks `origin/main` at
`https://github.com/NijatM/TF4DGS.git`. All commands below are reference commands
for the user to run in VS Code's PowerShell terminal. The assistant does not
perform commits or pushes.

## 1. Create the GitHub repositories

- [Create a new repository](https://github.com/new) named **TF4DGS** under
  **NijatM**. Leave it empty: do not generate a README, license or `.gitignore`.
- [Fork LichtFeld Studio](https://github.com/MrNeRF/LichtFeld-Studio/fork) under
  **NijatM**, retaining the name **LichtFeld-Studio**. vcpkg uses its upstream
  repository and does not need a fork.

Alternatively, create the repositories from PowerShell with GitHub CLI.
Install/login only if those steps are not already complete:

```powershell
winget install --id GitHub.cli --exact --source winget
$Gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
& $Gh auth login --web --git-protocol https
```

The current user already completed installation/login and both repository creations.
For an initial setup only, create the main repository with:

```powershell
& $Gh repo create NijatM/TF4DGS --private
```

Create the source fork with:

```powershell
& $Gh repo fork MrNeRF/LichtFeld-Studio --clone=false
```

Do not combine `--remote=false` with an explicit repository argument: GitHub
CLI 2.102.0 rejects that combination. The command above creates the fork without
cloning another checkout. The existing source `origin` URL is already configured.

For a fresh setup, configure Git author name/email for both local repositories.
The current user has already completed this step.
Replace `YOUR_GITHUB_EMAIL` below with a verified email or the exact noreply
address shown in [your GitHub email settings](https://github.com/settings/emails).
These commands configure only the two project repositories:

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
$GitEmail = 'YOUR_GITHUB_EMAIL'
git config user.name 'NijatM'
git config user.email $GitEmail
git -C .local/src/LichtFeld-Studio config user.name 'NijatM'
git -C .local/src/LichtFeld-Studio config user.email $GitEmail
```

## 2. Publish the existing packaging fix to your fork

The initial installation applied the CUDA 13 packaging fix to the upstream
source checkout. The user has now published that fix to their fork; its portable
patch is also saved in TF4DGS. The commands below document that completed
migration. Skip this section for the current setup and for later recursive
clones of the published project.

From the project folder, configure the fork and inspect the edit:

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
git -C .local/src/LichtFeld-Studio remote rename origin upstream
git -C .local/src/LichtFeld-Studio remote add origin https://github.com/NijatM/LichtFeld-Studio.git
git -C .local/src/LichtFeld-Studio switch -c tf4dgs
git -C .local/src/LichtFeld-Studio add CMakeLists.txt
git --no-pager -C .local/src/LichtFeld-Studio diff --cached
```

The staged edit should contain only the four-line CUDA `bin/x64` runtime
search fix. Commit and push it, then change the submodule URL:

The review commands use `--no-pager` to print directly to the terminal. If an
earlier command opened a viewer showing `:` or `(END)`, press **q** to exit it
and return to the PowerShell prompt.

```powershell
git -C .local/src/LichtFeld-Studio commit -m "Fix CUDA 13 Windows runtime dependency packaging"
git -C .local/src/LichtFeld-Studio push -u origin tf4dgs
git submodule set-url .local/src/LichtFeld-Studio https://github.com/NijatM/LichtFeld-Studio.git
```

Run this sequence once; if an individual command fails, resolve that error
before proceeding. Retrying from the beginning can collide with a remote or
branch that the earlier commands already created. Until the URL switch is
performed, `.gitmodules` deliberately uses the working upstream URL.

## 3. Review and make the first TF4DGS commit

```powershell
git add .
git status --short
git --no-pager diff --cached --stat
git --no-pager diff --cached --submodule=log
```

Expected contents: project Markdown, setup/test scripts, environment recipe,
Git configuration, the runtime patch, native dependency inventory, and two
submodule references. Source files inside the submodules are committed in
their own repositories; they do not become individual files in TF4DGS.

Excluded: downloaded installers, compiled programs, build/cache/log folders,
footage, reconstruction/training outputs, environments, local editor settings,
credentials, and machine-specific installation/validation/worker JSON files.
`PROJECT_MEMORY.md` preserves the useful machine checkpoint summaries.

After review:

```powershell
git commit -m "Initialize TF4DGS with pinned source submodules and reproducible Windows setup"
git remote add origin https://github.com/NijatM/TF4DGS.git
git push --recurse-submodules=check -u origin main
```

The push check verifies that referenced submodule commits are already available
on a submodule remote; it does not push the submodules for you. GitHub sign-in
may be requested by Git Credential Manager.

## 4. Clone on another machine

```powershell
git clone --recurse-submodules https://github.com/NijatM/TF4DGS.git
Set-Location -LiteralPath .\TF4DGS
```

Follow `INSTALLATION.md`. Native source pins come from TF4DGS's recorded
submodule commits. The working app, CUDA toolkit, Conda manager and build
dependencies still need installation/building on that machine.

## 5. Later source development

Keep LichtFeld modifications on a branch in your fork. Commit/push source edits
there first, then stage the resulting reference in TF4DGS with:

```powershell
git add .local/src/LichtFeld-Studio
```

The build helper reads that reference, so future fork commits do not require
editing a hardcoded LichtFeld commit in the installer. It still checks that
the checkout matches the recorded reference and preserves the selected
dependency baseline. Record and validate deliberate dependency upgrades.

Submodule checkout paths remain under `.local/src` to retain this machine's
working build paths. `.gitignore` exposes exactly those two submodule paths;
other `.local` content remains excluded. Their existing embedded Git metadata
is supported by Git; fresh recursive clones use Git's normal submodule layout.

The assistant must always leave commits and pushes to the user and provide
terminal commands with suitable commit messages. This includes pushes to the
LichtFeld fork. No automatic push scripts are part of this project.

References: [Git submodule commands](https://git-scm.com/docs/git-submodule),
[GitHub fork instructions](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo).
