# Claude 세션 실행기 (Windows PowerShell)
# 근거: Claude Code 공식 문서 https://code.claude.com/docs/en/cli-reference
#       https://code.claude.com/docs/en/claude-code-on-the-web
#       https://code.claude.com/docs/en/remote-control
#       https://code.claude.com/docs/en/github-actions

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$script:WorkDir = (Get-Location).Path

function Test-Claude {
    if (Get-Command claude -ErrorAction SilentlyContinue) { return $true }
    Write-Host ''
    Write-Host '[오류] claude 명령어를 찾을 수 없습니다.' -ForegroundColor Red
    Write-Host '메뉴 [I]에서 Claude Code를 설치합니다.'
    Pause-Return
    return $false
}

function Test-GitRepo {
    git -C $script:WorkDir rev-parse --is-inside-work-tree 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-InDir([scriptblock]$Block) {
    Push-Location $script:WorkDir
    try { & $Block } finally { Pop-Location }
}

function Get-GitHubUrl {
    if (-not (Test-GitRepo)) { return $null }
    $remote = git -C $script:WorkDir remote get-url origin 2>$null
    if (-not $remote) { return $null }
    $remote = $remote.Trim()
    if ($remote -match 'github\.com[:/](.+?)(\.git)?$') { return "https://github.com/$($Matches[1])" }
    return $null
}

function Show-Menu {
    Clear-Host
    Write-Host '=============================================='
    Write-Host '        Claude 세션 실행기 (PC/클라우드/GitHub)'
    Write-Host '=============================================='
    Write-Host " 작업 폴더: $script:WorkDir"
    Write-Host '----------------------------------------------'
    Write-Host ' [PC 로컬 세션]'
    Write-Host '  1. 새 세션 시작                    claude'
    Write-Host '  2. 최근 세션 이어하기              claude -c'
    Write-Host '  3. 세션 목록에서 골라 재개         claude -r'
    Write-Host ' [PC 세션을 앱·웹에서 조작]'
    Write-Host '  4. 원격 제어 켜고 세션 시작        claude --remote-control'
    Write-Host '  5. 원격 제어 서버 실행             claude remote-control'
    Write-Host ' [클라우드 세션]'
    Write-Host '  6. 클라우드 새 세션 생성           claude --cloud'
    Write-Host '  7. 클라우드 세션을 PC로 가져오기   claude --teleport'
    Write-Host '  8. 웹 브라우저로 열기              claude.ai/code'
    Write-Host ' [GitHub]'
    Write-Host '  9. GitHub 저장소 페이지 열기'
    Write-Host '  G. GitHub 앱 연동 설정             /install-github-app'
    Write-Host ' [설정]'
    Write-Host '  D. 작업 폴더 변경'
    Write-Host '  I. Claude Code 설치·버전 확인'
    Write-Host '  0. 종료'
    Write-Host '=============================================='
}

function Pause-Return { Write-Host ''; Read-Host '엔터를 누르면 메뉴로 돌아갑니다' | Out-Null }

while ($true) {
    Show-Menu
    $sel = (Read-Host '번호 선택').Trim().ToUpper()
    switch ($sel) {
        '1' { if (Test-Claude) { Invoke-InDir { claude } } }
        '2' { if (Test-Claude) { Invoke-InDir { claude -c } } }
        '3' { if (Test-Claude) { Invoke-InDir { claude -r } } }
        '4' {
            if (Test-Claude) {
                Write-Host '조건: Pro·Max·Team·Enterprise 계정 로그인. API 키 로그인은 지원하지 않습니다.'
                $name = Read-Host '세션 이름 (엔터 시 폴더명)'
                if (-not $name) { $name = Split-Path $script:WorkDir -Leaf }
                Invoke-InDir { claude --remote-control $name }
            }
        }
        '5' {
            if (Test-Claude) {
                Write-Host '이 PC를 Claude 앱·claude.ai에서 조작할 수 있게 대기합니다. 종료는 Ctrl+C 입니다.'
                $name = Read-Host '서버 이름 (엔터 시 폴더명)'
                if (-not $name) { $name = Split-Path $script:WorkDir -Leaf }
                Invoke-InDir { claude remote-control --name $name }
            }
        }
        '6' {
            if (Test-Claude) {
                if (Test-GitRepo) {
                    Write-Host '주의: 클라우드는 GitHub 원격 저장소의 현재 브랜치를 복제합니다. 먼저 git push 하십시오.' -ForegroundColor Yellow
                }
                $task = Read-Host '클라우드에 맡길 작업 내용'
                if ($task) { Invoke-InDir { claude --cloud $task } }
                else { Write-Host '작업 내용이 비어 취소합니다.' }
            }
        }
        '7' {
            if (Test-Claude) {
                Write-Host '조건: 같은 저장소 폴더, 커밋되지 않은 변경 없음, 같은 claude.ai 계정.'
                $id = Read-Host '세션 ID (엔터 시 목록에서 선택)'
                if ($id) { Invoke-InDir { claude --teleport $id } }
                else { Invoke-InDir { claude --teleport } }
            }
        }
        '8' { Start-Process 'https://claude.ai/code' }
        '9' {
            $url = Get-GitHubUrl
            if ($url) { Start-Process $url }
            else { Write-Host '작업 폴더에 GitHub 원격 저장소(origin)가 없습니다.'; Pause-Return }
        }
        'G' {
            if (Test-Claude) {
                Write-Host '조건: 저장소 관리자 권한, GitHub CLI 로그인(gh auth login).'
                Write-Host 'Claude가 열리면 /install-github-app 을 입력하십시오.'
                Write-Host '설정 후 이슈·PR 댓글에 @claude 를 적으면 Claude가 작업합니다.'
                Read-Host '엔터를 누르면 Claude를 엽니다' | Out-Null
                Invoke-InDir { claude }
            }
        }
        'D' {
            $dir = Read-Host '새 작업 폴더 경로'
            if ($dir -and (Test-Path $dir -PathType Container)) { $script:WorkDir = (Resolve-Path $dir).Path }
            else { Write-Host '폴더가 없습니다.'; Pause-Return }
        }
        'I' {
            if (Get-Command claude -ErrorAction SilentlyContinue) {
                claude --version
            } else {
                $ans = Read-Host '설치하시겠습니까? (Y/N)'
                if ($ans -match '^[Yy]') { Invoke-Expression (Invoke-RestMethod 'https://claude.ai/install.ps1') }
            }
            Pause-Return
        }
        '0' { return }
        default { Write-Host '잘못된 입력입니다.'; Start-Sleep -Seconds 1 }
    }
}
