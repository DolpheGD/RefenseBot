import discord

from bot.utils.embedder import get_danger_color
from datetime import datetime, timedelta, timezone

class LeaderboardView(discord.ui.View):
    def __init__(self, users, server_name, author_id):
        super().__init__(timeout=300)
        self.author_id = author_id

        self.current_page = 0
        self.pages = [
            users[i:i+10]
            for i in range(0, len(users), 10)
        ]
        self.server_name = server_name
        self.update_buttons()
        


    def create_embed(self):
        page = self.pages[self.current_page]
        
        color = get_danger_color(page[0].danger_score)

        embed = discord.Embed(
            title=f" 🏆 Danger Leaderboard for {self.server_name} 🏆 ",
            color=color
        )

        if page[0].avatar_url:
            embed.set_thumbnail(url=page[0].avatar_url)


        for i, user in enumerate(page, start=1):
            if user.display_name:
                name = user.display_name
            else:
                name = 'Unknown User'

            placement = i + self.current_page * 10
            embed.add_field(
                name=f"{placement}. {name}\n",
                value=f"Danger: {user.danger_score:.2%}",
                inline=False
            )

        embed.set_footer(
            text=f"Page {self.current_page + 1}/{len(self.pages)}"
        )

        return embed


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the message author can use this button.",
                ephemeral=True
            )
            return False
        return True
    

    @discord.ui.button(
        label="⬅️",
        style=discord.ButtonStyle.secondary
    )
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.current_page > 0:
            self.current_page -= 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )



    @discord.ui.button(
        label="➡️",
        style=discord.ButtonStyle.secondary
    )
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )



    def update_buttons(self):
        self.previous.disabled = self.current_page == 0

        self.next.disabled = (
            self.current_page == len(self.pages) - 1
        )




class VoteView(discord.ui.View):
    def __init__(self, last_voted):
        super().__init__(timeout=300)
        self.last_voted = last_voted
        self.add_item(
            discord.ui.Button(
                label="Vote",
                url= "https://top.gg/bot/1518822102596190308",
                style=discord.ButtonStyle.link
            )
        )

    def create_embed(self):
        last_voted = self.last_voted

        if last_voted is not None and last_voted.tzinfo is None:
            last_voted = last_voted.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if last_voted is None:
            can_vote = True
        else:
            next_vote = last_voted + timedelta(hours=12)
            can_vote = now >= next_vote

        if can_vote:
            embed = discord.Embed(
                title=f"🗳️ Vote for RefenseBot",
                description="✅ **You may vote now!**",
                color=discord.Color.green()
            )
        else:
            remaining = next_vote - now

            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            embed = discord.Embed(
                title="🕒 Vote Cooldown",
                description=(
                    "You have already voted.\n"
                    f"**Come back in:** `{hours}h {minutes}m`"
                ),
                color=discord.Color.orange()
            )

        embed.set_footer(text="Thank you for supporting RefenseBot!")

        return embed

