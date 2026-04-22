from __future__ import annotations


def split_text_recursive(
    text: str,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
    separators: tuple[str, ...] = ("\n\n", "\n", "。", "！", "？", ".", "!", "?", ";", "；", ",", "，", " "),
) -> list[str]:
    """
    一个轻量的递归字符切分器：
    - 先按大分隔符切，再逐步降级分隔符
    - 最终按固定窗口切分并加 overlap

    设计取舍：
    - 不引入额外依赖（如 LangChain），方便你“从 0 到 1”理解与改造
    - 优先保持段落/句子边界，尽量减少“切断语义”的情况
    - 当文本没有合适分隔符或片段过长时，才降级到硬窗口切分
    """
    t = (text or "").strip()
    if not t:
        return []
    if chunk_size <= 0:
        return [t]
    if chunk_overlap < 0:
        chunk_overlap = 0
    if chunk_overlap >= chunk_size:
        # overlap 过大容易导致有效信息密度下降，这里做一个保守降级，避免无限重叠。
        chunk_overlap = max(0, chunk_size // 5)

    def merge_with_overlap(parts: list[str]) -> list[str]:
        merged: list[str] = []
        buf = ""
        for p in parts:
            p = (p or "").strip()
            if not p:
                continue
            if not buf:
                buf = p
                continue
            if len(buf) + 1 + len(p) <= chunk_size:
                buf = f"{buf}\n{p}"
            else:
                merged.append(buf)
                buf = p
        if buf:
            merged.append(buf)
        return merged

    def hard_window(s: str) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(s):
            j = min(len(s), i + chunk_size)
            out.append(s[i:j].strip())
            if j >= len(s):
                break
            i = max(0, j - chunk_overlap)
        return [x for x in out if x]

    def rec(s: str, seps: tuple[str, ...]) -> list[str]:
        if len(s) <= chunk_size:
            return [s.strip()]
        if not seps:
            return hard_window(s)
        sep = seps[0]
        if sep and sep in s:
            parts = [x for x in s.split(sep)]
            merged = merge_with_overlap(parts)
            out: list[str] = []
            for m in merged:
                if len(m) <= chunk_size:
                    out.append(m.strip())
                else:
                    out.extend(rec(m, seps[1:]))
            return [x for x in out if x]
        return rec(s, seps[1:])

    return rec(t, separators)

