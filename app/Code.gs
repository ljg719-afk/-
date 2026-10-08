/**
 * 공공건축 네트워크 명단앱 - 서버 코드 (Google Apps Script)
 * 시트 구성: 명단 / 계정 / 접속기록 / 수정이력(자동 생성)
 * 권한: 마스터(전체) / 편집자(명단 수정) / 열람자(조회)
 */

const SHEET_LIST = '명단';
const SHEET_USER = '계정';
const SHEET_LOG = '접속기록';
const SHEET_HIST = '수정이력';
const ROLES = ['열람자', '편집자'];   // 앱에서 부여 가능한 권한
const EDIT_COLS = ['업체', '성명', '직급', '직책', '년생', '빠른년생', '띠', '출신학교', '비고'];
const ZODIAC = ['쥐띠', '소띠', '호랑이띠', '토끼띠', '용띠', '뱀띠', '말띠', '양띠', '원숭이띠', '닭띠', '개띠', '돼지띠'];
const SESSION_SEC = 21600;   // 세션 유지 6시간 (CacheService 최대값)
const MAX_FAIL = 5;          // 연속 실패 허용 횟수
const LOCK_SEC = 600;        // 잠금 시간 10분
const MIN_PW_LEN = 8;        // 비밀번호 최소 길이

/* ---------- 웹앱 진입 ---------- */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('공공건축 네트워크')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=1');
}

/* ---------- 시트 메뉴 (최초 마스터 설정용) ---------- */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('명단앱 관리')
    .addItem('마스터 계정 최초 설정', 'setupMaster')
    .addToUi();
}

function setupMaster() {
  const ui = SpreadsheetApp.getUi();
  const sh = sheet_(SHEET_USER);
  const exists = sh.getDataRange().getValues().slice(1).some(r => r[1] === '마스터');
  if (exists) { ui.alert('마스터 계정이 이미 있습니다. 변경은 앱 화면에서 하십시오.'); return; }
  const id = ui.prompt('마스터 아이디 입력').getResponseText().trim();
  const pw = ui.prompt('마스터 비밀번호 입력 (' + MIN_PW_LEN + '자 이상)').getResponseText();
  if (!id || !pw || pw.length < MIN_PW_LEN) { ui.alert('입력값이 올바르지 않습니다.'); return; }
  const salt = Utilities.getUuid();
  sh.appendRow([id, '마스터', salt, hash_(pw, salt), 'Y', '']);
  ui.alert('마스터 계정이 생성되었습니다.');
}

/* ---------- 공통 함수 ---------- */
function sheet_(name) { return SpreadsheetApp.getActive().getSheetByName(name); }

function hash_(pw, salt) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, salt + pw, Utilities.Charset.UTF_8);
  return bytes.map(b => ('0' + (b & 0xff).toString(16)).slice(-2)).join('');
}

function findUser_(id) {
  const sh = sheet_(SHEET_USER);
  const v = sh.getDataRange().getValues();
  for (let i = 1; i < v.length; i++) {
    if (String(v[i][0]) === id) {
      return { row: i + 1, id: v[i][0], role: v[i][1], salt: v[i][2], hash: v[i][3], active: v[i][4] === 'Y' };
    }
  }
  return null;
}

function log_(id, kind, result) {
  sheet_(SHEET_LOG).appendRow([new Date(), id, kind, result]);
}

function session_(token) {
  if (!token) throw new Error('로그인이 필요합니다.');
  const s = CacheService.getScriptCache().get('tok_' + token);
  if (!s) throw new Error('세션이 만료되었습니다. 다시 로그인하십시오.');
  return JSON.parse(s);
}

function master_(token) {
  const s = session_(token);
  if (s.role !== '마스터') throw new Error('마스터 권한이 필요합니다.');
  return s;
}

function editor_(token) {
  const s = session_(token);
  if (s.role !== '마스터' && s.role !== '편집자') throw new Error('명단 수정 권한이 없습니다.');
  return s;
}

function checkPw_(pw) {
  if (!pw || pw.length < MIN_PW_LEN) throw new Error('비밀번호는 ' + MIN_PW_LEN + '자 이상이어야 합니다.');
}

/* ---------- 로그인 / 로그아웃 ---------- */
function login(id, pw) {
  id = String(id || '').trim();
  const cache = CacheService.getScriptCache();
  const failKey = 'fail_' + id;
  const fails = Number(cache.get(failKey) || 0);
  if (fails >= MAX_FAIL) { log_(id, '로그인', '잠금'); throw new Error('로그인 실패가 반복되어 10분간 잠겼습니다.'); }

  const u = findUser_(id);
  if (!u || !u.active || hash_(pw, u.salt) !== u.hash) {
    cache.put(failKey, String(fails + 1), LOCK_SEC);
    log_(id, '로그인', '실패');
    throw new Error('아이디 또는 비밀번호가 올바르지 않습니다.');
  }
  cache.remove(failKey);
  const token = Utilities.getUuid();
  cache.put('tok_' + token, JSON.stringify({ id: u.id, role: u.role }), SESSION_SEC);
  sheet_(SHEET_USER).getRange(u.row, 6).setValue(new Date());
  log_(id, '로그인', '성공');
  return { token: token, id: u.id, role: u.role };
}

function logout(token) {
  CacheService.getScriptCache().remove('tok_' + token);
}

/* ---------- 명단 조회 ---------- */
function getList(token) {
  session_(token);
  const v = sheet_(SHEET_LIST).getDataRange().getDisplayValues();
  const h = v.shift();
  return v.filter(r => r[2]).map(r => {
    const o = {};
    h.forEach((k, i) => o[k] = r[i]);
    return o;
  });
}

/* ---------- 명단 수정 (마스터·편집자) ---------- */
function headers_() {
  const sh = sheet_(SHEET_LIST);
  const h = sh.getRange(1, 1, 1, sh.getLastColumn()).getDisplayValues()[0];
  ['순번'].concat(EDIT_COLS).forEach(k => { if (h.indexOf(k) < 0) throw new Error('명단 시트에 [' + k + '] 열이 없습니다.'); });
  return h;
}

function findRow_(no) {
  const sh = sheet_(SHEET_LIST);
  const h = headers_();
  const c = h.indexOf('순번');
  const v = sh.getDataRange().getDisplayValues();
  for (let i = 1; i < v.length; i++) if (String(v[i][c]) === String(no)) return { row: i + 1, values: v[i], h: h };
  return null;
}

function toObj_(h, r) { const o = {}; h.forEach((k, i) => o[k] = r[i]); return o; }

// 수식 실행 방지: = + - @ 로 시작하는 텍스트는 문자로 저장
function safe_(s) { s = String(s == null ? '' : s).trim(); return /^[=+\-@]/.test(s) ? "'" + s : s; }

function clean_(p) {
  const o = {};
  EDIT_COLS.forEach(k => o[k] = safe_(p[k]));
  if (!o['성명']) throw new Error('성명을 입력하십시오.');
  if (!o['업체']) throw new Error('업체를 입력하십시오.');
  if (!/^\d{2}$/.test(o['년생'])) throw new Error('년생은 두 자리 숫자로 입력하십시오. (예: 76)');
  o['년생'] = Number(o['년생']);
  o['빠른년생'] = o['빠른년생'] === 'Y' ? 'Y' : '';
  if (!o['띠']) o['띠'] = ZODIAC[(1900 + o['년생'] - 4) % 12];
  return o;
}

function hist_(id, kind, no, before, after) {
  let sh = sheet_(SHEET_HIST);
  if (!sh) {
    sh = SpreadsheetApp.getActive().insertSheet(SHEET_HIST);
    sh.appendRow(['일시', '아이디', '구분', '순번', '변경전', '변경후']);
  }
  sh.appendRow([new Date(), id, kind, no, before ? JSON.stringify(before) : '', after ? JSON.stringify(after) : '']);
}

// 다른 사람이 먼저 수정했는지 확인 (불러온 시점의 값과 현재 시트 값 비교)
function checkSame_(f, orig) {
  if (!orig) return;
  const changed = EDIT_COLS.some(k => String(f.values[f.h.indexOf(k)]) !== String(orig[k] == null ? '' : orig[k]));
  if (changed) throw new Error('다른 사용자가 먼저 수정한 자료입니다. 새로고침 후 다시 시도하십시오.');
}

function saveRow(token, p, orig) {
  const s = editor_(token);
  const o = clean_(p);
  const lock = LockService.getScriptLock(); lock.waitLock(10000);
  try {
    const sh = sheet_(SHEET_LIST);
    if (p['순번']) {
      const f = findRow_(p['순번']);
      if (!f) throw new Error('해당 순번 자료가 없습니다. 새로고침 후 다시 시도하십시오.');
      checkSame_(f, orig);
      const before = toObj_(f.h, f.values);
      EDIT_COLS.forEach(k => sh.getRange(f.row, f.h.indexOf(k) + 1).setValue(o[k]));
      hist_(s.id, '수정', p['순번'], before, o);
      log_(s.id, '명단수정:' + p['순번'] + ' ' + o['성명'], '성공');
    } else {
      const h = headers_();
      const c = h.indexOf('순번');
      const nos = sh.getLastRow() > 1 ? sh.getRange(2, c + 1, sh.getLastRow() - 1, 1).getValues().map(r => Number(r[0]) || 0) : [];
      const no = Math.max(0, ...nos) + 1;
      o['순번'] = no;
      sh.appendRow(h.map(k => (k in o) ? o[k] : ''));
      hist_(s.id, '추가', no, null, o);
      log_(s.id, '명단추가:' + no + ' ' + o['성명'], '성공');
    }
  } finally { lock.releaseLock(); }
  return getList(token);
}

function deleteRow(token, no, orig) {
  const s = editor_(token);
  const lock = LockService.getScriptLock(); lock.waitLock(10000);
  try {
    const f = findRow_(no);
    if (!f) throw new Error('해당 순번 자료가 없습니다. 새로고침 후 다시 시도하십시오.');
    checkSame_(f, orig);
    const before = toObj_(f.h, f.values);
    sheet_(SHEET_LIST).deleteRow(f.row);
    hist_(s.id, '삭제', no, before, null);
    log_(s.id, '명단삭제:' + no + ' ' + before['성명'], '성공');
  } finally { lock.releaseLock(); }
  return getList(token);
}

/* ---------- 본인 비밀번호 변경 ---------- */
function changeMyPassword(token, oldPw, newPw) {
  const s = session_(token);
  checkPw_(newPw);
  const lock = LockService.getScriptLock(); lock.waitLock(10000);
  try {
    const u = findUser_(s.id);
    if (hash_(oldPw, u.salt) !== u.hash) throw new Error('현재 비밀번호가 올바르지 않습니다.');
    const salt = Utilities.getUuid();
    sheet_(SHEET_USER).getRange(u.row, 3, 1, 2).setValues([[salt, hash_(newPw, salt)]]);
    log_(s.id, '비밀번호변경', '성공');
  } finally { lock.releaseLock(); }
}

/* ---------- 마스터 전용: 열람자 관리 ---------- */
function listUsers(token) {
  master_(token);
  const v = sheet_(SHEET_USER).getDataRange().getDisplayValues().slice(1);
  return v.filter(r => r[0]).map(r => ({ id: r[0], role: r[1], active: r[4] === 'Y', last: r[5] }));
}

function addUser(token, id, pw, role) {
  const m = master_(token);
  id = String(id || '').trim();
  role = ROLES.indexOf(role) >= 0 ? role : '열람자';
  if (!id) throw new Error('아이디를 입력하십시오.');
  checkPw_(pw);
  const lock = LockService.getScriptLock(); lock.waitLock(10000);
  try {
    if (findUser_(id)) throw new Error('이미 있는 아이디입니다.');
    const salt = Utilities.getUuid();
    sheet_(SHEET_USER).appendRow([id, role, salt, hash_(pw, salt), 'Y', '']);
    log_(m.id, role + '추가:' + id, '성공');
  } finally { lock.releaseLock(); }
}

function setUserRole(token, id, role) {
  const m = master_(token);
  if (ROLES.indexOf(role) < 0) throw new Error('권한 값이 올바르지 않습니다.');
  const u = findUser_(id);
  if (!u) throw new Error('아이디가 없습니다.');
  if (u.role === '마스터') throw new Error('마스터 권한은 변경할 수 없습니다.');
  sheet_(SHEET_USER).getRange(u.row, 2).setValue(role);
  log_(m.id, '권한변경:' + id + '→' + role, '성공');
}

function setUserActive(token, id, active) {
  const m = master_(token);
  const u = findUser_(id);
  if (!u) throw new Error('아이디가 없습니다.');
  if (u.role === '마스터') throw new Error('마스터 계정은 중지할 수 없습니다.');
  sheet_(SHEET_USER).getRange(u.row, 5).setValue(active ? 'Y' : 'N');
  log_(m.id, (active ? '사용재개:' : '사용중지:') + id, '성공');
}

function resetUserPassword(token, id, newPw) {
  const m = master_(token);
  checkPw_(newPw);
  const u = findUser_(id);
  if (!u) throw new Error('아이디가 없습니다.');
  if (u.role === '마스터') throw new Error('마스터 비밀번호는 [내 비밀번호 변경]에서 바꾸십시오.');
  const salt = Utilities.getUuid();
  sheet_(SHEET_USER).getRange(u.row, 3, 1, 2).setValues([[salt, hash_(newPw, salt)]]);
  log_(m.id, '비밀번호초기화:' + id, '성공');
}
