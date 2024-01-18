from os import environ as env

try:
    import config
except ImportError:
    config = None

VALID_SECRETS = (
    "BOT_TOKEN",
    "MONGO_URL",
    "BLOXLINK_API_KEY",
    "LINEAR_API_KEY",
)

for secret in VALID_SECRETS:
    globals()[secret] = env.get(secret) or getattr(config, secret, "")
