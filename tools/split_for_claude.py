# -*- coding: utf-8 -*-
"""
Claude 컨텍스트 첨부용 파일 분할 스크립트 (원본은 수정하지 않음)

- PDF : 페이지 단위로 분할하여 각 파일을 기준 용량(기본 10MB) 이하로 저장
- 그 외: 기준 이하 파일은 그대로 복사, 초과 파일은 목록에 보고
- 결과: 원본 폴더 옆 "<폴더명>_분할본" 폴더에 저장

사용법 (Windows 명령 프롬프트):
    pip install pypdf
    python split_for_claude.py "C:\\Users\\Dddd5\\OneDrive\\문서\\제혜영\\00  2027년 적용예정 표준교재"
    python split_for_claude.py "<폴더 경로>" 30     (기준 용량 MB 지정, 생략 시 10MB)
"""
import io
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

LIMIT_MB = 10
LIMIT = LIMIT_MB * 1024 * 1024
SAFETY = 0.95  # 저장 시 오버헤드 대비 여유분


def writer_size(writer):
    buf = io.BytesIO()
    writer.write(buf)
    return buf.tell(), buf.getvalue()


def build(reader, start, end):
    w = PdfWriter()
    for i in range(start, end):
        w.add_page(reader.pages[i])
    w.compress_identical_objects()
    return w


def split_pdf(src, out_dir):
    reader = PdfReader(str(src))
    total = len(reader.pages)
    parts, start = [], 0
    while start < total:
        # 이진 탐색으로 기준 용량 이하가 되는 최대 페이지 수 결정
        lo, hi, best = start + 1, total, None
        while lo <= hi:
            mid = (lo + hi) // 2
            size, data = writer_size(build(reader, start, mid))
            if size <= LIMIT * SAFETY:
                best = (mid, data)
                lo = mid + 1
            else:
                hi = mid - 1
        if best is None:  # 단일 페이지가 기준 용량 초과
            size, data = writer_size(build(reader, start, start + 1))
            best = (start + 1, data)
            print(f"  [경고] {start + 1}페이지 단독 {size / 1048576:.1f}MB ({LIMIT_MB}MB 초과)")
        end, data = best
        parts.append((start + 1, end, data))
        start = end
    for n, (s, e, data) in enumerate(parts, 1):
        name = f"{src.stem}_part{n:02d}_p{s:04d}-{e:04d}.pdf"
        (out_dir / name).write_bytes(data)
        print(f"  -> {name} ({len(data) / 1048576:.1f}MB)")


def main():
    global LIMIT_MB, LIMIT
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if len(sys.argv) > 2:
        LIMIT_MB = float(sys.argv[2])
        LIMIT = int(LIMIT_MB * 1024 * 1024)
    src_root = Path(sys.argv[1])
    out_root = src_root.parent / f"{src_root.name}_분할본"
    oversize = []
    for src in sorted(p for p in src_root.rglob("*") if p.is_file()):
        out_dir = out_root / src.relative_to(src_root).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        size = src.stat().st_size
        print(f"{src.relative_to(src_root)} ({size / 1048576:.1f}MB)")
        if size <= LIMIT:
            shutil.copy2(src, out_dir / src.name)
            print(f"  -> {LIMIT_MB}MB 이하, 그대로 복사")
        elif src.suffix.lower() == ".pdf":
            split_pdf(src, out_dir)
        else:
            oversize.append(src)
            print(f"  -> {LIMIT_MB}MB 초과 비PDF 파일, 수동 처리 필요")
    print(f"\n완료: {out_root}")
    if oversize:
        print("수동 처리 필요 파일 (PDF로 변환 후 재실행 권장):")
        for p in oversize:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
