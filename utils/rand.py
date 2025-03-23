import random
import struct

import aiohttp
from loguru import logger

import config


class RandomSource:
    PYRANDOM = "pyrandom"
    RANDOMORG = "random.org"
    YEBISU = "yebi.su"


async def _pyrandom(min_val, max_val, is_dice=False):
    if is_dice:
        return [random.randint(1, max_val) for _ in range(min_val)]
    return random.randint(min_val, max_val)


async def _get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


async def generate_unbiased_numbers(data, min_val, max_val, count):
    mod = max_val - min_val + 1
    max_acceptable = (1 << 64) // mod * mod
    numbers = []
    data_len = len(data)
    bytes_needed = count * 8
    
    if data_len < bytes_needed:
        logger.warning("Not enough data for unbiased generation")
        return None
    
    for i in range(count):
        chunk = data[i*8 : (i+1)*8]
        number = struct.unpack("<Q", chunk)[0]
        
        while number >= max_acceptable:
            number = (number >> 1)
        
        numbers.append((number % mod) + min_val)
    
    return numbers


async def generate(source, min_val, max_val, count=1):
    total_bytes = count * 8
    try:
        data = await _get(f"{source}{total_bytes}")
    except Exception as e:
        logger.debug(f"Data fetch error: {e}")
        data = b''
    
    if len(data) >= total_bytes:
        result = await generate_unbiased_numbers(data, min_val, max_val, count)
        if result is not None:
            return result
    
    logger.info("Using fallback random generator")
    if count == 1:
        return [await _pyrandom(min_val, max_val)]
    return await _pyrandom(min_val, max_val, is_dice=True)


async def _randomorg(min_val, max_val, is_dice=False):
    count = min_val if is_dice else 1
    actual_min = 1 if is_dice else min_val
    actual_max = max_val if is_dice else max_val
    
    numbers = await generate(
        "https://www.random.org/cgi-bin/randbyte?nbytes=",
        actual_min,
        actual_max,
        count
    )
    
    return numbers if is_dice else numbers[0]


async def _trng_yebisu(min_val, max_val, is_dice=False):
    count = min_val if is_dice else 1
    actual_min = 1 if is_dice else min_val
    actual_max = max_val if is_dice else max_val
    
    numbers = await generate(
        "https://yebi.su/api/pool?count=",
        actual_min,
        actual_max,
        count
    )
    
    return numbers if is_dice else numbers[0]


SOURCES = {
    RandomSource.PYRANDOM: _pyrandom,
    RandomSource.RANDOMORG: _randomorg,
    RandomSource.YEBISU: _trng_yebisu,
}


async def randint(min_val, max_val):
    try:
        return await SOURCES[config.random_source](min_val, max_val)
    except Exception as e:
        logger.error(f"{config.random_source}: {e}. Fallback to PYRANDOM.")
        return await _pyrandom(min_val, max_val)


async def rolldices(count, sides):
    try:
        return await SOURCES[config.random_source](count, sides, is_dice=True)
    except Exception as e:
        logger.error(f"{config.random_source}: {e}. Fallback to PYRANDOM.")
        return await _pyrandom(count, sides, is_dice=True)
