from bot.services.get_users import set_user_banned


async def sync_bans(bot):

    for guild in bot.guilds:

        async for ban in guild.bans():

            await set_user_banned(
                ban.user.id,
                guild.id,
                True
            )