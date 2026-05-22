import hashlib
from typing import Union


def sha256_hash(data: Union[str, bytes]) -> str:
    """
    Calculate SHA-256 hash of data.

    Args:
        data: String or bytes to hash

    Returns:
        Hexadecimal string representation of the SHA-256 hash
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    return hashlib.sha256(data).hexdigest()


def sha256_hash_file(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string representation of the SHA-256 hash
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Verify that a file matches the expected SHA-256 hash.

    Args:
        file_path: Path to the file
        expected_hash: Expected hexadecimal hash string

    Returns:
        True if file hash matches expected hash, False otherwise
    """
    return sha256_hash_file(file_path) == expected_hash