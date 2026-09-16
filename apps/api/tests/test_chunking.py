from app.services.chunking import split_blocks
from app.services.parsing import ParsedBlock


def test_split_blocks_groups_short_paragraphs() -> None:
    blocks = [
        ParsedBlock(text="First paragraph.", paragraph_index=0),
        ParsedBlock(text="Second paragraph.", paragraph_index=1),
    ]

    chunks = split_blocks(blocks)

    assert len(chunks) == 1
    assert "First paragraph." in chunks[0].text
    assert "Second paragraph." in chunks[0].text

