#!/usr/bin/env bash
# Claude 세션 실행기 (macOS / Linux / WSL)
# 근거: Claude Code 공식 문서 https://code.claude.com/docs/en/cli-reference
#       https://code.claude.com/docs/en/claude-code-on-the-web
#       https://code.claude.com/docs/en/remote-control
#       https://code.claude.com/docs/en/github-actions

WORKDIR="$(pwd)"

has_claude() {
  if command -v claude >/dev/null 2>&1; then return 0; fi
  echo
  echo "[오류] claude 명령어를 찾을 수 없습니다."
  echo "메뉴 [I]에서 Claude Code를 설치합니다."
  pause_return
  return 1
}

is_git_repo() { git -C "$WORKDIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; }

github_url() {
  is_git_repo || return 1
  local remote
  remote="$(git -C "$WORKDIR" remote get-url origin 2>/dev/null)" || return 1
  if [[ "$remote" =~ github\.com[:/](.+)$ ]]; then
    echo "https://github.com/${BASH_REMATCH[1]%.git}"
  else
    return 1
  fi
}

open_url() {
  if command -v open >/dev/null 2>&1; then open "$1"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1"
  elif command -v wslview >/dev/null 2>&1; then wslview "$1"
  else echo "브라우저에서 여십시오: $1"; pause_return
  fi
}

pause_return() { echo; read -r -p "엔터를 누르면 메뉴로 돌아갑니다 " _; }

in_dir() { (cd "$WORKDIR" && "$@"); }

show_menu() {
  clear 2>/dev/null
  cat <<EOF
==============================================
       Claude 세션 실행기 (PC/클라우드/GitHub)
==============================================
 작업 폴더: $WORKDIR
----------------------------------------------
 [PC 로컬 세션]
  1. 새 세션 시작                    claude
  2. 최근 세션 이어하기              claude -c
  3. 세션 목록에서 골라 재개         claude -r
 [PC 세션을 앱·웹에서 조작]
  4. 원격 제어 켜고 세션 시작        claude --remote-control
  5. 원격 제어 서버 실행             claude remote-control
 [클라우드 세션]
  6. 클라우드 새 세션 생성           claude --cloud
  7. 클라우드 세션을 PC로 가져오기   claude --teleport
  8. 웹 브라우저로 열기              claude.ai/code
 [GitHub]
  9. GitHub 저장소 페이지 열기
  G. GitHub 앱 연동 설정             /install-github-app
 [설정]
  D. 작업 폴더 변경
  I. Claude Code 설치·버전 확인
  0. 종료
==============================================
EOF
}

while true; do
  show_menu
  read -r -p "번호 선택: " sel
  case "${sel^^}" in
    1) has_claude && in_dir claude ;;
    2) has_claude && in_dir claude -c ;;
    3) has_claude && in_dir claude -r ;;
    4)
      if has_claude; then
        echo "조건: Pro·Max·Team·Enterprise 계정 로그인. API 키 로그인은 지원하지 않습니다."
        read -r -p "세션 이름 (엔터 시 폴더명): " name
        in_dir claude --remote-control "${name:-$(basename "$WORKDIR")}"
      fi ;;
    5)
      if has_claude; then
        echo "이 PC를 Claude 앱·claude.ai에서 조작할 수 있게 대기합니다. 종료는 Ctrl+C 입니다."
        read -r -p "서버 이름 (엔터 시 폴더명): " name
        in_dir claude remote-control --name "${name:-$(basename "$WORKDIR")}"
      fi ;;
    6)
      if has_claude; then
        is_git_repo && echo "주의: 클라우드는 GitHub 원격 저장소의 현재 브랜치를 복제합니다. 먼저 git push 하십시오."
        read -r -p "클라우드에 맡길 작업 내용: " task
        if [[ -n "$task" ]]; then in_dir claude --cloud "$task"
        else echo "작업 내용이 비어 취소합니다."; pause_return; fi
      fi ;;
    7)
      if has_claude; then
        echo "조건: 같은 저장소 폴더, 커밋되지 않은 변경 없음, 같은 claude.ai 계정."
        read -r -p "세션 ID (엔터 시 목록에서 선택): " id
        if [[ -n "$id" ]]; then in_dir claude --teleport "$id"; else in_dir claude --teleport; fi
      fi ;;
    8) open_url "https://claude.ai/code" ;;
    9)
      if url="$(github_url)"; then open_url "$url"
      else echo "작업 폴더에 GitHub 원격 저장소(origin)가 없습니다."; pause_return; fi ;;
    G)
      if has_claude; then
        echo "조건: 저장소 관리자 권한, GitHub CLI 로그인(gh auth login)."
        echo "Claude가 열리면 /install-github-app 을 입력하십시오."
        echo "설정 후 이슈·PR 댓글에 @claude 를 적으면 Claude가 작업합니다."
        read -r -p "엔터를 누르면 Claude를 엽니다 " _
        in_dir claude
      fi ;;
    D)
      read -r -p "새 작업 폴더 경로: " dir
      if [[ -n "$dir" && -d "$dir" ]]; then WORKDIR="$(cd "$dir" && pwd)"
      else echo "폴더가 없습니다."; pause_return; fi ;;
    I)
      if command -v claude >/dev/null 2>&1; then claude --version
      else
        read -r -p "설치하시겠습니까? (Y/N): " ans
        [[ "$ans" =~ ^[Yy] ]] && curl -fsSL https://claude.ai/install.sh | bash
      fi
      pause_return ;;
    0) exit 0 ;;
    *) echo "잘못된 입력입니다."; sleep 1 ;;
  esac
done
