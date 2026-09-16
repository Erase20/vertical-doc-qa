from dataclasses import dataclass

from app.core.config import settings
from app.services.parsing import ParsedBlock


@dataclass
class TextChunk:
    text: str
    token_count: int
    page_no: int | None
    section_path: list[str]
    paragraph_index: int | None
    char_start: int | None
    char_end: int | None


def approximate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def split_blocks(blocks: list[ParsedBlock]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    buffer: list[ParsedBlock] = []
    buffer_tokens = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens
        if not buffer:
            return
        text = "\n\n".join(block.text for block in buffer)
        first = buffer[0]
        last = buffer[-1]
        chunks.append(
            TextChunk(
                text=text,
                token_count=approximate_tokens(text),
                page_no=first.page_no,
                section_path=list(first.section_path),
                paragraph_index=first.paragraph_index,
                char_start=first.char_start,
                char_end=last.char_end,
            )
        )
        buffer = []
        buffer_tokens = 0

    for block in blocks:
        block_tokens = approximate_tokens(block.text)
        if block_tokens > settings.chunk_max_tokens:
            flush()
            chunks.extend(_split_long_block(block))
            continue

        if buffer and buffer_tokens + block_tokens > settings.chunk_target_tokens:
            flush()

        buffer.append(block)
        buffer_tokens += block_tokens

    flush()
    return _apply_overlap(chunks, settings.chunk_overlap_tokens)


def _split_long_block(block: ParsedBlock) -> list[TextChunk]:
    max_chars = settings.chunk_max_tokens * 2
    chunks: list[TextChunk] = []
    for offset in range(0, len(block.text), max_chars):
        text = block.text[offset : offset + max_chars]
        chunks.append(
            TextChunk(
                text=text,
                token_count=approximate_tokens(text),
                page_no=block.page_no,
                section_path=list(block.section_path),
                paragraph_index=block.paragraph_index,
                char_start=block.char_start,
                char_end=block.char_end,
            )
        )
    return chunks


def _apply_overlap(chunks: list[TextChunk], overlap_tokens: int) -> list[TextChunk]:
    if overlap_tokens <= 0:
        return chunks

    overlap_chars = overlap_tokens * 2
    for index in range(1, len(chunks)):
        previous = chunks[index - 1].text[-overlap_chars:]
        if previous:
            chunks[index].text = f"{previous}\n\n{chunks[index].text}"
            chunks[index].token_count = approximate_tokens(chunks[index].text)
    return chunks

