import discord
from bot.ml.classifier import classify_danger_level
from bot.services.update_user import get_top_ten_and_avg

def classify_with_output(message):
    """
    classify_danger_level output, using discord embeds
    """
    results = classify_danger_level(message)

    desc = ""
    for category, score in results.items():
        desc += f'{category}: {score:.2%}\n'

    color = get_danger_color(results["Danger"])

    embed = discord.Embed(
       title="**Results**",
       description=desc,
       color=color
    )

    return embed


def classify_user_with_output(user: discord.Member, verbose = False):
    top_ten, avg_danger = get_top_ten_and_avg(user.id)
    color = get_danger_color(avg_danger)

    
    embed = discord.Embed(
       title=f"**⚠️ {user.display_name}'s Danger ⚠️**",
       color=color
    )

    if len(top_ten) <= 0:
        value_output = "*[No Data]*"
        message_output = "*[No Data]*"
    else:
        value_output = f'{avg_danger:.2%}'
        message_output = ""
        for num, message in enumerate(top_ten):
            if verbose:
                message_output += f'{num}. "{message.content}" (Danger: {message.danger_score:.2%}) (ID: {message.message_id})\n'
            else:
                message_output += f'{num}. "{message.content}"\n'

    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name='Danger Score', value=value_output)
    embed.add_field(name='Messages', value=message_output, inline=False)

    return embed


def get_danger_color(danger):
    if danger > 1.0:
        color = 0 #black
    elif danger > 0.9:
        color = discord.Color.dark_red()
    elif danger > 0.8:
        color = discord.Color.red()
    elif danger > 0.65:
        color = discord.Color.orange()
    elif danger > 0.5:
        color = discord.Color.yellow()
    else:
        color = discord.Color.green()

    return color
    
