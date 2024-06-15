import random
import asyncio
from urllib.request import urlopen, Request
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    TRNGTXLYRE = "trng.txlyre.website"


def _pyrandom(min, max):
    return random.randint(min, max)


# TODO: make it sane
def _get(url):
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
        },
    )
    return urlopen(req).read().decode("ASCII")


def _randomorg(min, max):
    n = _get(
        f"https://www.random.org/integers/?num=1&min={min}&max={max}&format=plain&col=1&base=10"
    )
    return int(n)


def _trngtxlyre(min, max):
    n = _get(f"https://r.txlyre.website/getnum.php?min={min}&max={max}")
    return int(n)


SOURCES = {
    RandomSource.PYRANDOM: _pyrandom,
    RandomSource.RANDOMORG: _randomorg,
    RandomSource.TRNGTXLYRE: _trngtxlyre,
}


def randint(min, max):
    try:
        return SOURCES[config.random_source](min, max)
    except Exception as e:
        logger.error(f"{config.random_source}: {e}. Fallback to PYRANDOM.")

        return SOURCES[RandomSource.PYRANDOM](min, max)
