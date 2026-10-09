# Claude 세션 실행기

## 1. 개요
- 메뉴 번호로 Claude Code 세션을 엽니다.
- 열 수 있는 위치는 PC(로컬), 클라우드(claude.ai/code), GitHub입니다.
- 모든 명령어는 Claude Code 공식 문서에 근거합니다.

## 2. 파일 구성
| 파일 | 용도 |
|---|---|
| `claude-launcher.cmd` | Windows용입니다. 더블클릭으로 실행합니다. |
| `claude-launcher.ps1` | Windows PowerShell 본체입니다. |
| `claude-launcher.sh` | macOS·Linux·WSL용입니다. |

## 3. 실행 방법
- Windows 설치(최초 1회): PowerShell에 아래 한 줄을 붙여넣습니다.
  ```powershell
  irm https://raw.githubusercontent.com/ljg719-afk/-/claude/relaxed-hamilton-cdii2m/tools/claude-launcher/install-windows.ps1 | iex
  ```
- 설치 위치는 `%USERPROFILE%\claude-launcher`입니다. 이 폴더가 사용자 PATH에 추가됩니다.
- 설치 후 어느 폴더에서든 `claude-launcher`를 입력합니다.
- 설치하지 않은 경우: 파일이 있는 폴더에서 `.\claude-launcher.cmd`로 실행합니다. PowerShell은 현재 폴더의 파일을 `.\` 없이 실행하지 않습니다.
- macOS·Linux: 작업 폴더에서 `bash claude-launcher.sh`를 실행합니다.
- 실행한 위치가 작업 폴더가 됩니다. 메뉴 `D`에서 바꿀 수 있습니다.

## 4. 메뉴와 실행 명령
| 번호 | 기능 | 실행 명령 |
|---|---|---|
| 1 | PC 새 세션 | `claude` |
| 2 | 최근 세션 이어하기 | `claude -c` |
| 3 | 세션 골라 재개 | `claude -r` |
| 4 | 원격 제어 켜고 세션 시작 | `claude --remote-control "이름"` |
| 5 | 원격 제어 서버 실행 | `claude remote-control --name "이름"` |
| 6 | 클라우드 새 세션 생성 | `claude --cloud "작업 내용"` |
| 7 | 클라우드 세션을 PC로 가져오기 | `claude --teleport [세션ID]` |
| 8 | 웹으로 열기 | `https://claude.ai/code` |
| 9 | GitHub 저장소 페이지 열기 | origin 주소를 엽니다. |
| G | GitHub 앱 연동 | Claude 실행 후 `/install-github-app` 입력 |
| I | 설치·버전 확인 | `claude --version` 또는 공식 설치 스크립트 |

## 5. 사용 조건
- 원격 제어(4·5번)는 Pro·Max·Team·Enterprise 계정이 필요합니다. API 키 로그인은 지원하지 않습니다.
- 클라우드 세션(6번)은 GitHub 원격 저장소의 현재 브랜치를 복제합니다. PC의 변경분은 먼저 push해야 합니다.
- 가져오기(7번)는 같은 저장소 폴더, 깨끗한 git 상태, 같은 claude.ai 계정이 필요합니다.
- GitHub 연동(G)은 저장소 관리자 권한과 GitHub CLI 로그인(`gh auth login`)이 필요합니다.
- GitHub 연동 후 이슈·PR 댓글에 `@claude`를 적으면 Claude가 작업합니다.
- `--remote`는 `--cloud`의 구형 별칭입니다. 이 실행기는 `--cloud`를 사용합니다.

## 6. 설치 명령 (메뉴 I)
- Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
- macOS·Linux·WSL: `curl -fsSL https://claude.ai/install.sh | bash`

## 7. 근거 문서
- CLI 명령 참조: https://code.claude.com/docs/en/cli-reference
- 웹·클라우드 세션: https://code.claude.com/docs/en/claude-code-on-the-web
- 원격 제어: https://code.claude.com/docs/en/remote-control
- GitHub 연동: https://code.claude.com/docs/en/github-actions
- 설치: https://code.claude.com/docs/en/setup
