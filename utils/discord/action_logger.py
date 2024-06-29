from localization import locale


class DiscordLogger:
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, label, **kwargs):
        for key in kwargs:
            if kwargs is str:
                kwargs[key] = kwargs[key].replace('`', '')
        list_values = map(lambda key: locale.format(key, value=kwargs[key]), kwargs)
        text = "\n".join(list_values)
        text = f"[{getattr(locale, label)}] {text}"

        await self.bot.log_channel.send(text)
