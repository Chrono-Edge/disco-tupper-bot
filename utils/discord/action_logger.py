from localization import locale

class DiscordLogger:
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, label, **kwargs):
        text = "; ".join(map(lambda key: locale.format(key, value=kwargs[key]), kwargs))
        text = f"[{getattr(locale, label)}] {text}"

        await self.bot.log_channel.send(text)
