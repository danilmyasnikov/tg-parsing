from __future__ import annotations
import os
import json
import pathlib
from typing import TypedDict, NamedTuple

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class Config(TypedDict, total=False):
    targets: list[str]



def load_config() -> list[str]:
    cfg_path = pathlib.Path('config.json')
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
            if isinstance(cfg, dict):
                return cfg.get('targets', []) or []
        except Exception as e:
            print('Warning: failed to read config.json:', e)
    return []


class Credentials(NamedTuple):
    api_id: int
    api_hash: str


def get_api_credentials() -> Credentials:
    api_id = os.getenv('TG_API_ID')
    api_hash = os.getenv('TG_API_HASH')
    if api_id is None or api_hash is None:
        raise RuntimeError('TG_API_ID and TG_API_HASH must be set (or provide a .env file)')
    try:
        return Credentials(int(api_id), api_hash)
    except ValueError:
        raise RuntimeError('TG_API_ID must be an integer')
