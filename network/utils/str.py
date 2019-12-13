import random

# Constants
ALPHABET = 'abcdefghijklmnopqrstuvwxyz0123456789'


# Utils
def generate_random_str(size: int) -> str:
    return ''.join(random.choice(ALPHABET) for _ in range(size))
