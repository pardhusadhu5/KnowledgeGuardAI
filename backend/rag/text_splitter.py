from typing import List


def split_text_into_chunks(text: str, chunk_size: int = 400, chunk_overlap: int = 60) -> List[str]:
    """
    Recursively splits text into overlapping chunks, prioritizing paragraphs and sentences.
    """
    if not text:
        return []

    # If text is shorter than chunk_size, return it directly
    if len(text) <= chunk_size:
        return [text.strip()]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If paragraph itself is larger than chunk_size, split by sentences
            if len(para) > chunk_size:
                sentences = [s.strip() for s in para.replace(".\n", ". ").split(". ") if s.strip()]
                current_sentence_chunk = ""
                for sent in sentences:
                    sentence_with_dot = sent if sent.endswith(".") else f"{sent}."
                    if len(current_sentence_chunk) + len(sentence_with_dot) + 1 <= chunk_size:
                        current_sentence_chunk = f"{current_sentence_chunk} {sentence_with_dot}".strip()
                    else:
                        if current_sentence_chunk:
                            chunks.append(current_sentence_chunk)
                        current_sentence_chunk = sentence_with_dot
                if current_sentence_chunk:
                    chunks.append(current_sentence_chunk)
                current_chunk = ""
            else:
                # Add overlap from previous chunk if available
                if chunks and chunk_overlap > 0:
                    prev = chunks[-1]
                    overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
                    current_chunk = f"{overlap_text} {para}".strip()
                else:
                    current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    # Filter out empty or whitespace-only chunks
    return [c.strip() for c in chunks if c.strip()]
