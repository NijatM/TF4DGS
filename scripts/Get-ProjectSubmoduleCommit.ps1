# Dot-source after Git is available. Use the parent repository's recorded
# gitlink rather than freezing the trainer to its original upstream revision.
function Get-ProjectSubmoduleCommit {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ProjectRoot,
        [Parameter(Mandatory)][string]$RelativePath
    )
    $IndexEntry = (& git.exe -C $ProjectRoot ls-files --stage -- $RelativePath | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Could not read the project submodule reference.' }
    if ($IndexEntry -notmatch '^160000 ([0-9a-f]{40}) 0\t') {
        throw "No staged/committed submodule reference for $RelativePath. Follow GIT_SETUP.md or clone TF4DGS with --recurse-submodules."
    }
    return $Matches[1]
}
