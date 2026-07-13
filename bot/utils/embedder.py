import discord
from bot.ml.all_classifier import classify_message_and_image
from bot.services.get_users import get_is_banned, get_top_ten_and_avg, get_total_messages, get_vote_count

async def classify_with_output(content: str, message_id: str = "", attachments: list[discord.Attachment] = []):
    """
    classify_danger_level output, using discord embeds
    """
    results, new_content, is_image = await classify_message_and_image(content, message_id, attachments)

    if len(new_content) > 100:
        desc = f'"{new_content[:100]} (...)"'
    else:
        desc = f'"{new_content}"'

    if is_image:
        desc += f'\n(Has image attachment)'

    value = ""
    for category, score in results.items():
        value += f'{category}: {score:.2%}\n'

    color = get_danger_color(results["Danger"])

    embed = discord.Embed(
       title="**Results**",
       description=desc,
       color=color
    )

    embed.add_field(name="Breakdown", value=value, inline=False)

    return embed



async def classify_user_with_output(user: discord.Member, verbose = False):
    """
    returns a discord embed of the top 10 most dangerous messages for the user, and their average danger score
    """
    top_ten, avg_danger = await get_top_ten_and_avg(user.id, user.guild)
    total_messages = await get_total_messages(user.id, user.guild)
    votes, votes_used = await get_vote_count(user.id, user.guild)
    is_banned = await get_is_banned(user.id, user.guild)

    color = get_danger_color(avg_danger)


    desc = f"Danger Score: {avg_danger:.2%}\nTotal Messages: {total_messages}\nVotes: {votes}\nVotes used: {votes_used}"
    if is_banned:
        desc += "\n**Banned**"
    card_achieve_text = get_danger_card_achievement(avg_danger)
    message_achieve_text = get_message_count_achievement(total_messages)
    desc += '\n\n**Achievements:**\n' + card_achieve_text + '\n' + message_achieve_text
    
    if len(top_ten) > 0:
        worst_achieve = get_worst_message_achievement(top_ten[0].danger_score)
        if worst_achieve is not None:
            desc += f'\n{worst_achieve}'

    embed = discord.Embed(
       title=f"**⚠️ {user.display_name}'s Danger ⚠️**",
       color=color,
       description=desc
    )
    
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    

    if len(top_ten) <= 0:
        embed.add_field(name='*[No Data]*', value="", inline=False)
        return embed
    

    for num, message in enumerate(top_ten, start=1):
        name_text = f'{num}. '
        if len(message.content) >= 50:
            name_text += f'{message.content[:50]} (...)'
            if verbose:
                name_text += f' ({len(message.content) - 50} more)'
        else:
            name_text += message.content

        value_text = ""
        if verbose:
            value_text += f'(Danger: {message.danger_score:.2%}) (Hate: {message.hate_score:.2%}) (Sexual: {message.sexual_score:.2%}) (Concern: {message.concern_score:.2%}) (Scam: {message.scam_score:.2%}) (ID: {message.message_id})\n'

        embed.add_field(name=name_text, value=value_text, inline=False)

    return embed


def get_danger_color(danger):
    if danger > 1.5:
        color = discord.Color.from_rgb(48, 4, 51)
    elif danger > 1.2:
        color = 0 #black
    elif danger > 1.0:
        color = discord.Color.from_rgb(69, 38, 5)
    elif danger > 0.8:
        color = discord.Color.red()
    elif danger > 0.65:
        color = discord.Color.orange()
    elif danger > 0.5:
        color = discord.Color.yellow()
    elif danger > 0.25:
        color = discord.Color.green()
    else:
        color = discord.Color.blue()
    return color
    

def get_danger_card_achievement(danger):
    if danger > 1.5:
        card = "🟪 T-Card"
    elif danger > 1.2:
        card = "⬛ Black Card"
    elif danger > 1.0:
        card = "🟫 Brown Card"
    elif danger > 0.8:
        card = "🟥 Red Card"
    elif danger > 0.65:
        card = "🟧 Orange Card"
    elif danger > 0.5:
        card = "🟨 Yellow Card"
    elif danger > 0.25:
        card = "🟩 Green Card"
    else:
        card = "🟦 Blue Card"
    return card


def get_message_count_achievement(message_count):
    if message_count >= 100000:
        message = f'☄️ Chat God'
    elif message_count >= 50000:
        message = f'👑 The Chosen Chatter ({message_count}/100000)'
    elif message_count >= 10000:
        message = f'🌟 No Life Chatter ({message_count}/50000)'
    elif message_count >= 5000:
        message = f'⭐ Ultimate Chatter ({message_count}/10000)'
    elif message_count >= 2500:
        message = f'✨ Devoted Chatter ({message_count}/5000)'
    elif message_count >= 1000:
        message = f'💫 Dedicated Chatter ({message_count}/2500)'
    elif message_count >= 500:
        message = f'🏅 Frequent Chatter ({message_count}/1000)'
    elif message_count >= 250:
        message = f'🥈 Regular Chatter ({message_count}/500)'
    elif message_count >= 100:
        message = f'🥉 Chatter ({message_count}/250)'
    elif message_count >= 25:
        message = f'🌲 New Chatter ({message_count}/100)'
    else:
        message = f'🪦 Unknown Chatter ({message_count}/25)'

    return message


def get_worst_message_achievement(worst_danger):
    if worst_danger >= 3.0:
        message = f'☠️ Abhorrent Message'
    elif worst_danger >= 2.5:
        message = f'😵 Atrocious Message'
    elif worst_danger >= 2.0:
        message = f'🤮 Vile Message'
    elif worst_danger >= 1.5:
        message = f'😭 Terrible Message'
    elif worst_danger >= 1.0:
        message = f'🚨 Alarming Message'
    else:
        return None
    
    return message