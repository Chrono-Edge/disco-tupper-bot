import random

import aiohttp
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    TRNGTXLYRE = "trng.txlyre.website"
    TRNGIIKE = "trng.iike.ru"


async def _pyrandom(min, max, is_dice=False):
    if is_dice:
        rolls = []
        for _ in range(min):
            rolls.append(random.randint(1, max))

        return rolls

    return random.randint(min, max)


async def _get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


async def _randomorg(min, max, is_dice=False):
    if is_dice:
        raise NotImplemented

    n = await _get(
        f"https://www.random.org/integers/?num=1&min={min}&max={max}&format=plain&col=1&base=10"
    )
    return int(n)


async def _trngtxlyre(min, max, is_dice=False):
    if is_dice:
        raise NotImplemented

    n = await _get(f"https://r.txlyre.website/getnum.php?min={min}&max={max}")
    return int(n)


async def _trngiikeru(min, max, is_dice=False):
    if is_dice:
        n = await _get(
            f"https://trng.iike.ru/api/numbers?min=1&max={max}&count={min}&fallback_to_prng=1"
        )
        ns = n.split(" ")
        ns = map(int, ns)

        return list(ns)

    n = await _get(
        f"https://trng.iike.ru/api/numbers?min={min}&max={max}&fallback_to_prng=1"
    )
    return int(n)


SOURCES = {
    RandomSource.PYRANDOM: _pyrandom,
    RandomSource.RANDOMORG: _randomorg,
    RandomSource.TRNGTXLYRE: _trngtxlyre,
    RandomSource.TRNGIIKE: _trngiikeru,
}


async def randint(min, max):
    try:
        return await SOURCES[config.random_source](min, max)
    except Exception as e:
        logger.error(f"{config.random_source}: {e}. Fallback to PYRANDOM.")

        return await SOURCES[RandomSource.PYRANDOM](min, max)


async def rolldices(count, sides):
    try:
        return await SOURCES[config.random_source](count, sides, is_dice=True)
    except Exception as e:
        logger.error(f"{config.random_source}: {e}. Fallback to PYRANDOM.")

        return await SOURCES[RandomSource.PYRANDOM](count, sides, is_dice=True)
