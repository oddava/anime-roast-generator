import hashlib
import os
import random
import secrets

# Anime-themed name components
ANIME_PREFIXES = [
    "Weeb",
    "Otaku",
    "Anime",
    "Manga",
    "Chibi",
    "Kawaii",
    "Senpai",
    "Kouhai",
    "Tsundere",
    "Yandere",
    "Dandere",
    "Kuudere",
    "Waifu",
    "Husbando",
    "Loli",
    "Shota",
    "Sensei",
    "Ninja",
    "Samurai",
    "Shinigami",
    "Gundam",
    "Mecha",
    "Isekai",
    "Shounen",
    "Shoujo",
    "Seinen",
    "Josei",
    "Ecchi",
    "Harem",
    "Dragon",
    "Demon",
    "Angel",
    "Vampire",
    "Werewolf",
    "Neko",
    "Inu",
    "Sakura",
    "Sushi",
    "Ramen",
    "Baka",
    "Sugoi",
    "Kawaii",
    "Desu",
]

ANIME_SUFFIXES = [
    "Lord",
    "King",
    "Queen",
    "Master",
    "Slayer",
    "Hunter",
    "Fan",
    "Enjoyer",
    "Connoisseur",
    "Critic",
    "Weeb",
    "Otaku",
    "Senpai",
    "Kouhai",
    "Chan",
    "Kun",
    "San",
    "Sama",
    "Sensei",
    "Ninja",
    "Samurai",
    "Warrior",
    "Hero",
    "Villain",
    "Protagonist",
    "Antagonist",
    "Sidekick",
    "NPC",
    "Gamer",
    "Watcher",
    "Binger",
    "Marathoner",
    "Collector",
    "Hoarder",
]


def generate_random_name() -> str:
    """Generate a random anime-themed username.

    Format: PrefixSuffix_XXX where XXX is a random number
    Example: WeebLord_420, AnimeEnjoyer_1337
    """
    prefix = random.choice(ANIME_PREFIXES)
    suffix = random.choice(ANIME_SUFFIXES)
    number = random.randint(1, 9999)

    return f"{prefix}{suffix}_{number}"


def hash_ip(ip_address: str) -> str:
    """Hash IP address for privacy-compliant rate limiting.

    Uses SHA-256 with a salt from environment variable to prevent rainbow table attacks.
    Raises ValueError if IP_HASH_SALT is not set.
    """
    salt = os.getenv("IP_HASH_SALT")
    if not salt:
        raise ValueError(
            "IP_HASH_SALT environment variable must be set for IP hashing. "
            "Generate a secure random string and set it in your .env file."
        )

    # Combine IP with salt and hash
    data = f"{ip_address}{salt}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_user_id() -> str:
    """Generate a unique user identifier for tracking without login."""
    return secrets.token_urlsafe(16)
