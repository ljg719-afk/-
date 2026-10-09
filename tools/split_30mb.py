# -*- coding: utf-8 -*-
"""폴더 내 파일을 30MB 이하 복사본으로 저장한다.

- PDF: 페이지 단위로 분할한다. 원본은 변경하지 않는다.
- 30MB 이하 파일: 그대로 복사한다.
- 30MB 초과 비PDF 파일: 바이트 분할 시 열 수 없으므로 목록만 출력한다.

사용법:
    pip install pypdf
    python split_30mb.py "원본폴더" "저장폴더"
"""
import io
import math
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

LIMIT = 30 * 1024 * 1024   # 30MB 상한
TARGET = 25 * 1024 * 1024  # 여유를 둔 목표 크기


def write_pages(reader, start, end):
    writer = PdfWriter()
    for i in range(start, end):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def split_range(reader, start, end, out):
    data = write_pages(reader, start, end)
    if len(data) <= LIMIT or end - start == 1:
        out.append((start, end, data))
        return
    mid = (start + end) // 2
    split_range(reader, start, mid, out)
    split_range(reader, mid, end, out)


def split_pdf(src, dst_dir):
    reader = PdfReader(str(src))
    total = len(reader.pages)
    n = max(1, math.ceil(src.stat().st_size / TARGET))
    step = math.ceil(total / n)
    parts = []
    for s in range(0, total, step):
        split_range(reader, s, min(s + step, total), parts)
    for idx, (s, e, data) in enumerate(parts, 1):
        name = f"{src.stem}_part{idx:02d}_p{s + 1}-{e}.pdf"
        (dst_dir / name).write_bytes(data)
        flag = "" if len(data) <= LIMIT else "  ※ 단일 페이지 30MB 초과"
        print(f"  {name}  {len(data) / 1048576:.1f}MB{flag}")


def main(src_root, dst_root):
    src_root, dst_root = Path(src_root), Path(dst_root)
    skipped = []
    for f in sorted(src_root.rglob("*")):
        if not f.is_file():
            continue
        dst_dir = dst_root / f.parent.relative_to(src_root)
        dst_dir.mkdir(parents=True, exist_ok=True)
        size = f.stat().st_size
        if size <= LIMIT:
            shutil.copy2(f, dst_dir / f.name)
            print(f"[복사] {f.name}  {size / 1048576:.1f}MB")
        elif f.suffix.lower() == ".pdf":
            print(f"[분할] {f.name}  {size / 1048576:.1f}MB")
            split_pdf(f, dst_dir)
        else:
            skipped.append(f)
    if skipped:
        print("\n[미처리] 30MB 초과 비PDF 파일. PDF로 변환 후 재실행 필요.")
        for f in skipped:
            print(f"  {f}  {f.stat().st_size / 1048576:.1f}MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
