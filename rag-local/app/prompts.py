from __future__ import annotations


SYSTEM_PROMPT = """你是一个严谨的中文助手。你必须只依据我提供的“参考资料片段”来回答问题。
如果参考资料不足以回答，就明确说“资料不足”，并给出你还需要哪些信息。
回答要简洁，尽量使用要点列表。"""


def build_prompt(query: str, contexts: list[str]) -> str:
    # 这里把检索到的片段编号，方便模型在回答中“指认来源”，也便于你在前端做引用高亮。
    ctx = "\n\n".join([f"[片段 {i+1}]\n{c}" for i, c in enumerate(contexts)]) if contexts else "（无）"
    return f"""# 参考资料片段
{ctx}

# 用户问题
{query}

# 作答要求
- 仅使用参考资料片段
- 引用片段编号（例如：见片段 2）
"""

