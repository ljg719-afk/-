# -*- coding: utf-8 -*-
"""
요양보호사 문제 폴더 -> 16:9 문제풀이 PPT 생성기

사용법 (Windows 명령 프롬프트):
    pip install python-pptx python-docx
    python make_quiz_ppt.py "C:\\Users\\Dddd5\\OneDrive\\문서\\제혜영\\24 요양보호사 문제"

- 폴더 안의 "한 파일 = 한 문제" 파일을 파일명 속 번호(1~80) 순으로 슬라이드화한다.
- 지원 형식: .txt / .docx (텍스트) , .png / .jpg / .jpeg / .bmp / .gif (이미지)
- 텍스트 파일 안의 "정답: ③" / "해설: ..." 줄을 정답 박스로 분리한다.
- 이미지 문제의 정답은 같은 폴더의 "정답.txt" 또는 "정답.csv"(형식: 번호,정답,해설)에서 읽는다.
- 정답 박스는 클릭 시 나타나는 페이드 애니메이션으로 설정된다.
- 누락 번호·중복 번호·정답 미확인 번호를 화면과 "누락번호_보고.txt"에 기록한다.
"""
import copy
import os
import re
import sys

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

TOTAL = 80
FONT = "맑은 고딕"

# 눈의 피로를 줄이는 짙은 브라운 계열 팔레트
BG = RGBColor(0x3B, 0x2A, 0x20)        # 배경: 짙은 브라운
BAR = RGBColor(0x2A, 0x1D, 0x16)       # 상단 띠: 더 짙은 브라운
TEXT = RGBColor(0xF3, 0xE9, 0xDC)      # 본문: 크림색
ACCENT = RGBColor(0xE0, 0xB8, 0x7A)    # 번호·강조: 연한 황토색
ANS_BG = RGBColor(0x5A, 0x40, 0x2E)    # 정답 박스 배경
ANS_LINE = RGBColor(0xE0, 0xB8, 0x7A)

TEXT_EXT = {".txt", ".docx"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
ANSWER_FILES = {"정답.txt", "정답.csv"}

ANS_RE = re.compile(r"^\s*[\[【(]?\s*(정답|답)\s*[\]】)]?\s*[:：.]?\s*(.*)$")
EXP_RE = re.compile(r"^\s*[\[【(]?\s*(해설|풀이)\s*[\]】)]?\s*[:：.]?\s*(.*)$")
CIRCLED = "①②③④⑤⑥"


# ---------------------------------------------------------------- 파일 읽기
def read_text_file(path):
    for enc in ("utf-8-sig", "cp949", "utf-16"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("인코딩 판별 실패: " + path)


def read_docx(path):
    import docx
    d = docx.Document(path)
    lines = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            lines.append(" | ".join(c.text for c in row.cells))
    return "\n".join(lines)


def question_number(filename):
    """파일명 속 숫자 중 1~TOTAL 범위의 마지막 숫자를 문제 번호로 본다."""
    stem = os.path.splitext(filename)[0]
    nums = [int(n) for n in re.findall(r"\d+", stem)]
    nums = [n for n in nums if 1 <= n <= TOTAL]
    return nums[-1] if nums else None


def split_question(raw):
    """본문에서 정답/해설 줄을 분리한다."""
    body, answer, expl = [], [], []
    mode = "body"
    for line in raw.replace("\r", "").split("\n"):
        m_a, m_e = ANS_RE.match(line), EXP_RE.match(line)
        if m_a:
            mode = "ans"
            if m_a.group(2).strip():
                answer.append(m_a.group(2).strip())
            continue
        if m_e:
            mode = "exp"
            if m_e.group(2).strip():
                expl.append(m_e.group(2).strip())
            continue
        {"body": body, "ans": answer, "exp": expl}[mode].append(line)
    body_text = "\n".join(body).strip()
    # 맨 앞 "12." / "12)" / "문제 12." 형태 번호 제거 (슬라이드 제목에 번호 표시)
    body_text = re.sub(r"^\s*(문제\s*)?\d{1,2}\s*[.)번]\s*", "", body_text)
    # 한 줄에 붙은 보기(① ② ...)를 줄바꿈
    body_text = re.sub(r"\s*([%s])" % CIRCLED, r"\n\1", body_text).strip()
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)
    return body_text, " ".join(a for a in answer if a.strip()).strip(), "\n".join(e for e in expl if e.strip()).strip()


def load_answer_sheet(folder):
    """정답.txt / 정답.csv : 한 줄에 '번호,정답[,해설]' 또는 '번호 정답 해설'."""
    sheet = {}
    for name in ANSWER_FILES:
        p = os.path.join(folder, name)
        if not os.path.exists(p):
            continue
        for line in read_text_file(p).splitlines():
            m = re.match(r"^\s*(\d{1,2})\s*[,.\t)번 ]\s*([^,\t]+?)\s*(?:[,\t]\s*(.*))?$", line)
            if m and 1 <= int(m.group(1)) <= TOTAL:
                sheet[int(m.group(1))] = (m.group(2).strip(), (m.group(3) or "").strip())
    return sheet


# ---------------------------------------------------------------- 슬라이드 도구
def fill_bg(slide):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG


def add_text(slide, x, y, w, h, text, size, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(size * 0.35)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = FONT
        rpr = r._r.get_or_add_rPr()
        ea = rpr.find(qn("a:ea"))
        if ea is None:
            ea = etree.SubElement(rpr, qn("a:ea"))
        ea.set("typeface", FONT)
    return tb


def fit_size(text, base, box_chars_per_line, max_lines):
    """글자 수에 맞춰 글꼴 크기를 줄인다(대략치)."""
    size = base
    while size > 14:
        cpl = box_chars_per_line * base / size
        lines = sum(max(1, -(-len(l) // int(cpl))) for l in text.split("\n"))
        if lines * size <= max_lines * base:
            break
        size -= 2
    return size


def add_click_fade(slide, shape):
    """shape 를 '클릭 시 나타내기(페이드)' 애니메이션으로 설정."""
    spid = shape.shape_id
    xml = f"""
<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
  <p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
   <p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>
    <p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
     <p:par><p:cTn id="5" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">
      <p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
       <p:set><p:cBhvr><p:cTn id="6" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
        <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
        <p:to><p:strVal val="visible"/></p:to></p:set>
       <p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="7" dur="500"/>
        <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>
      </p:childTnLst></p:cTn></p:par>
    </p:childTnLst></p:cTn></p:par>
   </p:childTnLst></p:cTn></p:par>
  </p:childTnLst></p:cTn>
  <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
  <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
 </p:childTnLst></p:cTn></p:par></p:tnLst>
 <p:bldLst><p:bldP spid="{spid}" grpId="0" animBg="1"/></p:bldLst>
</p:timing>"""
    slide.element.append(etree.fromstring(xml))


def header(slide, prs, title, sub=""):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.9))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BAR
    bar.line.fill.background()
    add_text(slide, Inches(0.5), Inches(0.12), Inches(6), Inches(0.7), title, 30, ACCENT, True,
             anchor=MSO_ANCHOR.MIDDLE)
    if sub:
        add_text(slide, Inches(7), Inches(0.12), Inches(5.8), Inches(0.7), sub, 14, TEXT,
                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


def answer_box(slide, prs, answer, expl, top):
    h = prs.slide_height - top - Inches(0.3)
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), top,
                                 prs.slide_width - Inches(1.0), h)
    box.adjustments[0] = 0.08
    box.fill.solid()
    box.fill.fore_color.rgb = ANS_BG
    box.line.color.rgb = ANS_LINE
    box.line.width = Pt(1.5)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.3)
    txt = "정답  " + (answer or "(정답 미입력)")
    lines = [(txt, 24, ACCENT, True)]
    if expl:
        lines.append(("해설  " + expl, fit_size(expl, 16, 80, 3), TEXT, False))
    for i, (t, s, c, b) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = t
        r.font.size = Pt(s)
        r.font.color.rgb = c
        r.font.bold = b
        r.font.name = FONT
        etree.SubElement(r._r.get_or_add_rPr(), qn("a:ea")).set("typeface", FONT)
    add_click_fade(slide, box)
    return box


# ---------------------------------------------------------------- 메인
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    folder = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "요양보호사_문제_1-80.pptx")

    sheet = load_answer_sheet(folder)
    found, dup, skipped = {}, {}, []
    for name in sorted(os.listdir(folder)):
        ext = os.path.splitext(name)[1].lower()
        if name in ANSWER_FILES or name.startswith("~$") or name.endswith(".pptx"):
            continue
        if ext not in TEXT_EXT | IMG_EXT:
            skipped.append(name)
            continue
        n = question_number(name)
        if n is None:
            skipped.append(name)
            continue
        if n in found:
            dup.setdefault(n, [found[n]]).append(name)
            continue
        found[n] = name

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)  # 16:9
    blank = prs.slide_layouts[6]
    W, H = prs.slide_width, prs.slide_height

    # 표지
    s = prs.slides.add_slide(blank)
    fill_bg(s)
    add_text(s, Inches(1), Inches(2.4), W - Inches(2), Inches(1.2), "요양보호사 문제풀이", 48, ACCENT, True,
             PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    add_text(s, Inches(1), Inches(3.7), W - Inches(2), Inches(0.8), f"1번 ~ {TOTAL}번", 26, TEXT,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    no_answer = []
    for n in range(1, TOTAL + 1):
        if n not in found:
            continue
        name = found[n]
        path = os.path.join(folder, name)
        ext = os.path.splitext(name)[1].lower()
        s = prs.slides.add_slide(blank)
        fill_bg(s)
        header(s, prs, f"문제 {n}", f"{n} / {TOTAL}")
        ans_top = H - Inches(1.75)

        if ext in IMG_EXT:
            from PIL import Image
            with Image.open(path) as im:
                iw, ih = im.size
            max_w, max_h = W - Inches(1.0), ans_top - Inches(1.15)
            scale = min(max_w / iw, max_h / ih)
            pw, ph = int(iw * scale), int(ih * scale)
            s.shapes.add_picture(path, int((W - pw) / 2), Inches(1.05), pw, ph)
            answer, expl = sheet.get(n, ("", ""))
        else:
            raw = read_docx(path) if ext == ".docx" else read_text_file(path)
            body, answer, expl = split_question(raw)
            if not answer and n in sheet:
                answer, expl = sheet[n]
            size = fit_size(body, 26, 46, 10)
            add_text(s, Inches(0.6), Inches(1.1), W - Inches(1.2), ans_top - Inches(1.2), body, size)

        if not answer:
            no_answer.append(n)
        answer_box(s, prs, answer, expl, ans_top)

    prs.save(out)

    missing = [n for n in range(1, TOTAL + 1) if n not in found]
    report = [
        f"생성 파일: {out}",
        f"인식된 문제 수: {len(found)} / {TOTAL}",
        "누락 번호: " + (", ".join(map(str, missing)) if missing else "없음"),
        "정답 미확인 번호: " + (", ".join(map(str, no_answer)) if no_answer else "없음"),
        "중복 번호(첫 파일만 사용): " + ("; ".join(f"{k}번={v}" for k, v in sorted(dup.items())) if dup else "없음"),
        "제외 파일(형식 미지원 또는 번호 없음): " + (", ".join(skipped) if skipped else "없음"),
        "",
        "[번호-파일 대응표]",
    ] + [f"{n:>2}번 : {found[n]}" for n in sorted(found)]
    text = "\n".join(report)
    print(text)
    with open(os.path.join(os.path.dirname(out) or ".", "누락번호_보고.txt"), "w", encoding="utf-8-sig") as f:
        f.write(text)


if __name__ == "__main__":
    main()
