import uuid

def generate_64bit_uuid():
    """Generates a unique signed 64-bit integer ID."""
    full_uuid = uuid.uuid4()
    uuid_int = full_uuid.int & ((1 << 64) - 1)  # keep lower 64 bits

    # Convert to signed range if needed
    if uuid_int >= 2**63:
        uuid_int -= 2**64

    return uuid_int

def generate_uuid_article_id():
    return str(uuid.uuid4())
