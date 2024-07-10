import random
import struct

import aiohttp
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    YEBISU = "yebi.su"


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
            return await resp.read()


async def generate(source, min, max, count=1):
    total = count * 8
    data = await _get(f"{source}{total}")

    numbers = []
    for i in range(count):
        number = struct.unpack("<Q", data[i * 8 : i * 8 + 8])[0]

        numbers.append(number % (max + 1 - min) + min)

    return numbers


async def _randomorg(min, max, is_dice=False):
    if is_dice:
        count = min
        min = 1
        max = max
    else:
        count = 1

    numbers = await generate(
        "https://www.random.org/cgi-bin/randbyte?nbytes=", min, max, count
    )

    if count == 1:
        return numbers[0]

    return numbers


async def _trng_yebisu(min, max, is_dice=False):
    if is_dice:
        count = min
        min = 1
        max = max
    else:
        count = 1

    numbers = await generate(f"https://yebi.su/api/pool?count=", min, max, count)

    if count == 1:
        return numbers[0]

    return numbers


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
