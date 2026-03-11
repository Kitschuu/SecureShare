import hashlib

def get_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compare_files_integrity(file1, file2):
    hash1 = get_file_hash(file1)
    hash2 = get_file_hash(file2)
    if hash1 == hash2:
        return True
    else:
        raise ValueError(f"File integrity check failed! \nOrig Hash: {hash1}\nDecr Hash: {hash2}")