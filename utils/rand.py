import random
import asyncio

import aiohttp
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    TRNGTXLYRE = "trng.txlyre.website"


def _pyrandom(min, max):
    return random.randint(min, max)


# TODO: make it sane
async def _get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


def _randomorg(min, max):
    n = asyncio.get_event_loop().run_until_complete(
        _get(
            f"https://www.random.org/integers/?num=1&min={min}&max={max}&format=plain&col=1&base=10"
        )
    )
    return int(n)


def _trngtxlyre(min, max):
    n = asyncio.get_event_loop().run_until_complete(
        _get(f"https://r.txlyre.website/getnum.php?min={min}&max={max}")
    )
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
