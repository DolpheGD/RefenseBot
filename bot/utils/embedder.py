import discord
from bot.ml.all_classifier import classify_message_and_image
from bot.services.get_users import get_is_banned, get_top_ten_and_avg, get_total_messages, get_vote_count

async def classify_with_output(content: str, message_id: str = "", attachments: list[discord.Attachment] | None = None):
    """
    classify_danger_level output, using discord embeds
    """
    if attachments is None:
        attachments = []

    results, new_content, is_image = await classify_message_and_image(content, message_id, attachments)

    if len(new_content) > 100:
        desc = f'"{new_content[:100]} (...)"'
    else:
        desc = f'"{new_content}"'

    if is_image:
        desc += f'\n(Has image attachment)'
        image_url = next(
            (attachment.url for attachment in attachments if attachment.content_type and attachment.content_type.startswith("image/")),
            ""
        )
        if image_url:
            desc += f'\nImage URL: {image_url}'

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



class UserClassificationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author_id: int):
        super().__init__(timeout=300)
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the command user can use these buttons.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page],
            view=self,
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page],
            view=self,
        )

    def update_buttons(self):
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page == len(self.embeds) - 1


async def classify_user_with_output(
    user: discord.Member,
    verbose: bool = False,
    message_limit: int = 10,
) -> tuple[discord.Embed, UserClassificationView | None]:
    """
    returns a Discord embed of the top 10 dangerous messages and the user's tier-weighted danger score
    """
    top_ten, avg_danger = await get_top_ten_and_avg(user.id, user.guild)
    total_messages = await get_total_messages(user.id, user.guild)
    votes, votes_used = await get_vote_count(user.id, user.guild)
    is_banned = await get_is_banned(user.id, user.guild)

    color = get_danger_color(avg_danger)

    # info
    desc = f"Danger Score: {avg_danger:.2%}"

    if verbose:
        desc += f'\nTotal Messages: {total_messages}\nVotes: {votes}\nVotes used: {votes_used}'
        if is_banned:
            desc += "\n**Banned**"

    #achievement info
    card_achieve_text = get_danger_card_achievement(avg_danger)
    message_achieve_text = get_message_count_achievement(total_messages)
    votes_achieve_text = get_voter_achievements(votes)
    vote_spend_text = get_vote_spender_achievements(votes_used)

    desc += '\n\n**Achievements:**\n' + card_achieve_text + '\n' + message_achieve_text
    
    if votes_achieve_text is not None:
        desc += f'\n{votes_achieve_text}'

    if vote_spend_text is not None:
        desc += f'\n{vote_spend_text}'

    if len(top_ten) > 0:
        worst_achieve = get_worst_message_achievement(top_ten[0].danger_score)
        if worst_achieve is not None:
            desc += f'\n{worst_achieve}'



    requested_messages = top_ten[:message_limit]
    pages = [
        requested_messages[start : start + 10]
        for start in range(0, len(requested_messages), 10)
    ] or [[]]
    embeds = []

    for page_number, page_messages in enumerate(pages, start=1):
        embed = discord.Embed(
            title=f"**⚠️ {user.display_name}'s Danger ⚠️**",
            color=color,
            description=desc,
        )

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        if not requested_messages:
            embed.add_field(name="*[No Data]*", value="", inline=False)
        else:
            for num, message in enumerate(
                page_messages,
                start=(page_number - 1) * 10 + 1,
            ):
                name_text = f"{num}. "
                if len(message.content) >= 50:
                    name_text += f"{message.content[:50]} (...)"
                    if verbose:
                        name_text += f" ({len(message.content) - 50} more)"
                else:
                    name_text += message.content

                value_text = ""
                if verbose:
                    value_text += (
                        f"(Danger: {message.danger_score:.2%}) "
                        f"(Hate: {message.hate_score:.2%}) "
                        f"(Sexual: {message.sexual_score:.2%}) "
                        f"(Concern: {message.concern_score:.2%}) "
                        f"(Scam: {message.scam_score:.2%}) "
                        f"(ID: {message.message_id})\n"
                    )
                    if message.image_url:
                        value_text += f"(Image: {message.image_url})\n"

                embed.add_field(name=name_text, value=value_text, inline=False)

        if len(pages) > 1:
            embed.set_footer(text=f"Page {page_number}/{len(pages)}")
        embeds.append(embed)

    view = UserClassificationView(embeds, user.id) if len(embeds) > 1 else None
    return embeds[0], view


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
    refense_emoji = "<:refense:1526107149338411069>"
    if message_count >= 1000000:
        message = f'{refense_emoji} True Refense'
    elif message_count >= 100000:
        message = f'☄️ The Chat God ({message_count}/1000000)'
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


def get_voter_achievements(vote_count):
    if vote_count >= 100:
        message = f'❤️‍🔥 Ultimate Voter'
    elif vote_count >= 50:
        message = f'🔥 Legendary Voter ({vote_count}/100)'
    elif vote_count >= 25:
        message = f'💌 Super Voter ({vote_count}/50)'
    elif vote_count >= 10:
        message = f'🗳️ Epic Voter ({vote_count}/25)'
    elif vote_count >= 5:
        message = f'📝 Frequent Voter ({vote_count}/10)'
    elif vote_count >= 3:
        message = f'📨 Regular Voter ({vote_count}/5)'
    elif vote_count >= 1:
        message = f'✉️ Voter ({vote_count}/3)'
    else:
        return None
        
    return message

def get_vote_spender_achievements(vote_spent):
    if vote_spent >= 50:
        message = f"🤯 The Past's Pulveriser"
    elif vote_spent >= 25:
        message = f'💥 History Eradicator ({vote_spent}/50)'
    elif vote_spent >= 10:
        message = f'💣 Danger Demolisher ({vote_spent}/25)'
    elif vote_spent >= 5:
        message = f'🧨 Danger Evader ({vote_spent}/10)'
    elif vote_spent >= 3:
        message = f'⚠️ Message Executor ({vote_spent}/5)'
    elif vote_spent >= 1:
        message = f'❌ Message Remover ({vote_spent}/3)'
    else:
        return None
    
    return message