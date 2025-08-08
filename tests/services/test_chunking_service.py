from ltms.services.chunking_service import (
    create_chunker, split_text_into_chunks, merge_small_chunks
)


def test_create_chunker_creates_valid_chunker():
    """Test that create_chunker creates a valid text chunker."""
    # Create chunker
    chunker = create_chunker(chunk_size=512, chunk_overlap=50)
    
    # Verify it's a valid chunker
    assert chunker is not None
    assert hasattr(chunker, 'split_text')
    
    # Test that we can split text
    test_text = "This is a test sentence. This is another sentence."
    chunks = split_text_into_chunks(chunker, test_text)
    
    # Verify chunks were created
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_split_text_into_chunks_creates_chunks():
    """Test that split_text_into_chunks creates proper text chunks."""
    # Create chunker
    chunker = create_chunker(chunk_size=100, chunk_overlap=20)
    
    # Test text splitting
    test_text = (
        "This is the first sentence. "
        "This is the second sentence. "
        "This is the third sentence. "
        "This is the fourth sentence."
    )
    
    chunks = split_text_into_chunks(chunker, test_text)
    
    # Verify chunks
    assert isinstance(chunks, list)
    assert len(chunks) > 1  # Should create multiple chunks
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk) > 0 for chunk in chunks)
    
    # Verify total content is preserved
    original_words = test_text.split()
    chunk_words = []
    for chunk in chunks:
        chunk_words.extend(chunk.split())
    
    # Should have same words (allowing for some differences due to chunking)
    assert len(original_words) <= len(chunk_words)


def test_split_text_into_chunks_handles_short_text():
    """Test that split_text_into_chunks handles short text correctly."""
    # Create chunker
    chunker = create_chunker(chunk_size=1000, chunk_overlap=100)
    
    # Test short text
    test_text = "This is a short text."
    chunks = split_text_into_chunks(chunker, test_text)
    
    # Verify result
    assert isinstance(chunks, list)
    assert len(chunks) == 1  # Should create single chunk
    assert chunks[0] == test_text


def test_split_text_into_chunks_handles_empty_text():
    """Test that split_text_into_chunks handles empty text gracefully."""
    # Create chunker
    chunker = create_chunker(chunk_size=100, chunk_overlap=20)
    
    # Test empty text
    chunks = split_text_into_chunks(chunker, "")
    
    # Verify result
    assert isinstance(chunks, list)
    assert len(chunks) == 0


def test_merge_small_chunks_combines_small_chunks():
    """Test that merge_small_chunks combines chunks that are too small."""
    # Create chunker
    chunker = create_chunker(chunk_size=100, chunk_overlap=20)
    
    # Test text that will create small chunks
    test_text = (
        "Sentence one. Sentence two. Sentence three. "
        "Sentence four. Sentence five. Sentence six."
    )
    
    chunks = split_text_into_chunks(chunker, test_text)
    merged_chunks = merge_small_chunks(chunks, min_chunk_size=50)
    
    # Verify merged chunks
    assert isinstance(merged_chunks, list)
    assert len(merged_chunks) <= len(chunks)  # Should have fewer or same chunks
    assert all(isinstance(chunk, str) for chunk in merged_chunks)
    assert all(len(chunk) >= 50 for chunk in merged_chunks)  # All chunks should be >= min size
