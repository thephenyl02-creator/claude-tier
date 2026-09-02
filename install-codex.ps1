# Codex Tier installer (Windows PowerShell 5.1+ / pwsh)
# irm https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install-codex.ps1 | iex

& {
    $Repo = 'thephenyl02-creator/claude-codex-tier'
    $Marketplace = 'codex-tier'
    $Plugin = 'codex-tier'
    $ZipUrl = "https://github.com/$Repo/archive/refs/heads/main.zip"
    $Marker = '.installed-by-codex-tier-installer'
    $Failed = $false

    function Write-Info($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
    function Write-Ok($Message)   { Write-Host "  + $Message" -ForegroundColor Green }
    function Write-Warn2($Message){ Write-Host "  ! $Message" -ForegroundColor Yellow }
    function Write-Err($Message)  { Write-Host "  x $Message" -ForegroundColor Red }

    $PreviousEap = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $InstallHome = if ($env:CODEX_TIER_INSTALL_HOME) {
            [IO.Path]::GetFullPath($env:CODEX_TIER_INSTALL_HOME)
        } else {
            [IO.Path]::GetFullPath($env:USERPROFILE)
        }
        $SkillsRoot = Join-Path $InstallHome '.agents\skills'
        $Destination = Join-Path $SkillsRoot $Plugin
        $LocalSource = $env:CODEX_TIER_SOURCE_ROOT
        $ForceDirect = ($env:CODEX_TIER_FORCE_DIRECT -eq '1')

        function Find-Codex {
            if ($env:CODEX_TIER_CODEX_BIN -and
                (Test-Path -LiteralPath $env:CODEX_TIER_CODEX_BIN)) {
                return [IO.Path]::GetFullPath($env:CODEX_TIER_CODEX_BIN)
            }
            $Command = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($Command -and $Command.Source) { return $Command.Source }
            $Candidates = @(
                (Join-Path $env:USERPROFILE '.local\bin\codex.exe'),
                (Join-Path $env:APPDATA 'npm\codex.cmd')
            )
            foreach ($Candidate in $Candidates) {
                if (Test-Path -LiteralPath $Candidate) { return $Candidate }
            }
            return $null
        }

        function Find-Python {
            foreach ($Name in @('python.exe', 'python3.exe', 'py.exe')) {
                $Command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue |
                    Select-Object -First 1
                if ($Command -and $Command.Source) { return $Command.Source }
            }
            return $null
        }

        function Invoke-Codex([string]$Binary, [string[]]$Arguments) {
            $global:LASTEXITCODE = $null
            try {
                $Output = @(& $Binary @Arguments 2>&1)
                return [pscustomobject]@{
                    Success = ($LASTEXITCODE -eq 0)
                    ExitCode = $LASTEXITCODE
                    Output = ($Output -join [Environment]::NewLine)
                }
            } catch {
                return [pscustomobject]@{
                    Success = $false
                    ExitCode = $null
                    Output = $_.Exception.Message
                }
            }
        }

        function Test-Source([string]$Source, [string]$Python) {
            if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md'))) { return $false }
            $Router = Join-Path $Source 'scripts\codex_tier.py'
            if (-not (Test-Path -LiteralPath $Router)) { return $false }
            $global:LASTEXITCODE = $null
            try {
                & $Python $Router validate *> $null
                return ($LASTEXITCODE -eq 0)
            } catch {
                return $false
            }
        }

        function Install-Direct([string]$Source, [string]$Python, [string]$TemporaryRoot) {
            if (-not (Test-Source $Source $Python)) {
                Write-Err "Codex Tier source validation failed at $Source"
                return $false
            }
            New-Item -ItemType Directory -Path $SkillsRoot -Force -ErrorAction Stop | Out-Null
            $ExpectedRoot = [IO.Path]::GetFullPath($SkillsRoot).TrimEnd('\') + '\'
            $ResolvedDestination = [IO.Path]::GetFullPath($Destination)
            if (-not $ResolvedDestination.StartsWith($ExpectedRoot,
                    [StringComparison]::OrdinalIgnoreCase) -or
                (Split-Path -Leaf $ResolvedDestination) -ne $Plugin) {
                Write-Err "Refusing unexpected destination: $ResolvedDestination"
                return $false
            }

            $Stage = Join-Path $TemporaryRoot 'codex-tier-stage'
            $Old = Join-Path $TemporaryRoot 'codex-tier-old'
            Remove-Item -LiteralPath $Stage,$Old -Recurse -Force -ErrorAction SilentlyContinue
            Copy-Item -LiteralPath $Source -Destination $Stage -Recurse -ErrorAction Stop
            New-Item -ItemType File -Path (Join-Path $Stage $Marker) -Force -ErrorAction Stop |
                Out-Null

            $HandBackup = $null
            if (Test-Path -LiteralPath $Destination) {
                if (Test-Path -LiteralPath (Join-Path $Destination $Marker)) {
                    Move-Item -LiteralPath $Destination -Destination $Old -ErrorAction Stop
                } else {
                    $HandBackup = Join-Path (Join-Path $InstallHome '.agents') (
                        'codex-tier-backup.' + (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss')
                    )
                    Move-Item -LiteralPath $Destination -Destination $HandBackup -ErrorAction Stop
                    Write-Warn2 "Existing hand-authored skill moved to $HandBackup"
                }
            }

            try {
                Move-Item -LiteralPath $Stage -Destination $Destination -ErrorAction Stop
                if (-not (Test-Source $Destination $Python)) {
                    throw 'installed copy failed deterministic validation'
                }
                Remove-Item -LiteralPath $Old -Recurse -Force -ErrorAction SilentlyContinue
                Write-Ok "Standalone skill installed at $Destination"
                return $true
            } catch {
                Remove-Item -LiteralPath $Destination -Recurse -Force -ErrorAction SilentlyContinue
                if (Test-Path -LiteralPath $Old) {
                    Move-Item -LiteralPath $Old -Destination $Destination -ErrorAction SilentlyContinue
                } elseif ($HandBackup -and (Test-Path -LiteralPath $HandBackup)) {
                    Move-Item -LiteralPath $HandBackup -Destination $Destination -ErrorAction SilentlyContinue
                }
                Write-Err "Install failed and the previous copy was restored: $($_.Exception.Message)"
                return $false
            }
        }

        function Invoke-PluginRoute([string]$Binary) {
            [void](Invoke-Codex $Binary @('plugin', 'marketplace', 'add', $Repo))
            [void](Invoke-Codex $Binary @('plugin', 'marketplace', 'upgrade', $Marketplace))
            $Add = Invoke-Codex $Binary @('plugin', 'add', "$Plugin@$Marketplace", '--json')
            if (-not $Add.Success) { return $false }
            $List = Invoke-Codex $Binary @('plugin', 'list', '--json')
            if (-not $List.Success) { return $false }
            try {
                $Parsed = $List.Output | ConvertFrom-Json
                return (@($Parsed.installed | Where-Object { $_.name -eq $Plugin }).Count -gt 0)
            } catch {
                return $false
            }
        }

        $CodexBinary = Find-Codex
        if (-not $CodexBinary) {
            Write-Err 'Codex was not found. Install the official CLI, then re-run:'
            Write-Err '  npm install --global @openai/codex'
            $Failed = $true
            return
        }
        $PythonBinary = Find-Python
        if (-not $PythonBinary) {
            Write-Err "Python 3 is required by Codex Tier's deterministic router."
            $Failed = $true
            return
        }

        $Version = Invoke-Codex $CodexBinary @('--version')
        $ExecHelp = Invoke-Codex $CodexBinary @('exec', '--help')
        $RequiredFlags = @('--model', '--config', '--json', '--output-last-message', '--sandbox')
        $CliCompatible = $Version.Success -and $ExecHelp.Success
        foreach ($Flag in $RequiredFlags) {
            if ($ExecHelp.Output -notmatch [regex]::Escape($Flag)) { $CliCompatible = $false }
        }
        $PackagedApp = ($CodexBinary -match '\\WindowsApps\\OpenAI\.Codex_')
        if ($CliCompatible) {
            Write-Ok "Codex: $($Version.Output.Trim())"
        } elseif ($PackagedApp) {
            Write-Warn2 'Codex Windows app detected, but its bundled CLI is not callable from this shell.'
            Write-Warn2 'Installing the standalone skill; native pinned app subagents remain available.'
            $ForceDirect = $true
        } else {
            Write-Err 'This Codex CLI does not expose the required pinned exec flags.'
            Write-Err 'Update it with: npm install --global @openai/codex'
            $Failed = $true
            return
        }

        $TemporaryRoot = Join-Path $env:TEMP (
            'codex-tier-' + [IO.Path]::GetRandomFileName()
        )
        New-Item -ItemType Directory -Path $TemporaryRoot -Force -ErrorAction Stop |
            Out-Null
        try {
            if ($LocalSource) {
                Write-Info 'Installing Codex Tier from local source...'
                $Source = Join-Path $LocalSource 'plugins\codex-tier\skills\codex-tier'
                if (-not (Install-Direct $Source $PythonBinary $TemporaryRoot)) {
                    $Failed = $true
                    return
                }
            } elseif (-not $ForceDirect -and (Invoke-PluginRoute $CodexBinary)) {
                Write-Ok "Plugin installed: $Plugin@$Marketplace"
                if (Test-Path -LiteralPath (Join-Path $Destination $Marker)) {
                    $OldDirect = Join-Path $TemporaryRoot 'old-direct'
                    Move-Item -LiteralPath $Destination -Destination $OldDirect -ErrorAction SilentlyContinue
                }
            } else {
                Write-Warn2 'Plugin route unavailable; installing the standalone skill.'
                $Archive = Join-Path $TemporaryRoot 'claude-tier.zip'
                Invoke-WebRequest -Uri $ZipUrl -OutFile $Archive -UseBasicParsing -ErrorAction Stop
                Expand-Archive -LiteralPath $Archive -DestinationPath $TemporaryRoot -Force -ErrorAction Stop
                # GitHub names the archive's top-level folder <repo>-<branch>.
                # Locate the folder that holds the skill instead of assuming the
                # repo name, so renaming the repository can never break this path.
                $Source = $null
                foreach ($Top in (Get-ChildItem -Path $TemporaryRoot -Directory -ErrorAction Stop)) {
                    $Candidate = Join-Path $Top.FullName 'plugins\codex-tier\skills\codex-tier'
                    if (Test-Path -LiteralPath (Join-Path $Candidate 'SKILL.md')) { $Source = $Candidate; break }
                }
                if (-not $Source) {
                    throw 'the downloaded archive did not contain plugins/codex-tier/skills/codex-tier - the repo layout may have changed.'
                }
                if (-not (Install-Direct $Source $PythonBinary $TemporaryRoot)) {
                    $Failed = $true
                    return
                }
            }
        } catch {
            Write-Err "Codex Tier installation failed: $($_.Exception.Message)"
            $Failed = $true
            return
        } finally {
            Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
        }

        Write-Host ''
        Write-Ok 'Done. Start a new Codex task, then invoke: $codex-tier'
    } finally {
        $ErrorActionPreference = $PreviousEap
        if ($Failed -and $PSCommandPath) { exit 1 }
    }
}
