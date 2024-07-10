import random

import aiohttp
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    YEBISU = "yebi.su"


# TODO make seed base generator and timeout to update
# TODO make count for generate numbers
# TODO make optimal class?

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
    random_hex_string = await _get(
        f"https://www.random.org/cgi-bin/randbyte?nbytes=32&format=h"
    )
    random_hex_string = random_hex_string.replace(" ", "")
    random.seed(random_hex_string)
    if is_dice:
        number_list = [random.randint(1, max) for _ in range(min)]
        return number_list

    return random.randint(min, max)


async def _trng_yebisu(min, max, is_dice=False):
    random_hex_string = await _get(
        f"https://yebi.su/api/pool?count=32&format=hexstring&mode=trng"
    )
    random.seed(random_hex_string)
    if is_dice:
        number_list = [random.randint(1, max) for _ in range(min)]
        return number_list

    return random.randint(min, max)


SOURCES = {
    RandomSource.PYRANDOM: _pyrandom,
    RandomSource.RANDOMORG: _randomorg,
    RandomSource.YEBISU: _trng_yebisu,
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
