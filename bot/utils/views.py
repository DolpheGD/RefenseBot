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






class AchievementGuideView(discord.ui.View):
    def __init__(self, author: discord.Member | discord.User):
        super().__init__(timeout=300)

        self.author = author
        self.page = 0
        self.max_pages = 6

        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the command author to use the buttons."""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ You cannot interact with someone else's achievement guide.",
                ephemeral=True
            )
            return False

        return True

    def update_buttons(self):
        self.left.disabled = self.page == 0
        self.right.disabled = self.page == self.max_pages - 1

    def create_embed(self) -> discord.Embed:

        embed = discord.Embed(
            title="📖 Refense Achievement Handbook",
            color=discord.Color.gold()
        )

        # ---------------- PAGE 0 ----------------

        if self.page == 0:

            embed.description = (
                "**Welcome to the Refense Achievement Handbook!**\n\n"
                "Achievements reward activity, participation and other accomplishments while using RefenseBot.\n\n"
                "Achievements shown on `/classify user` are earned automatically.\n\n"
                "**Categories**\n"
                "🃏 Danger Cards\n"
                "💬 Chatting\n"
                "☠️ Dangerous Messages\n"
                "🗳️ Voting\n"
                "💥 Vote Spending\n\n"
                "Use the buttons below to browse."
            )

        # ---------------- PAGE 1 ----------------

        elif self.page == 1:

            embed.description = (
                "**🃏 Danger Cards**\n\n"
                "Your danger card is determined by your overall danger rating.\n\n"
                "🟦 Blue Card — 0.00 - 0.25\n"
                "🟩 Green Card — 0.25 - 0.50\n"
                "🟨 Yellow Card — 0.50 - 0.65\n"
                "🟧 Orange Card — 0.65 - 0.80\n"
                "🟥 Red Card — 0.80 - 1.00\n"
                "🟫 Brown Card — 1.00 - 1.20\n"
                "⬛ Black Card — 1.20 - 1.50\n"
                "🟪 T-Card — 1.50+\n"
            )

        # ---------------- PAGE 2 ----------------

        elif self.page == 2:

            embed.description = (
                "**💬 Chatting Achievements**\n\n"
                "Earn these simply by chatting.\n\n"
                "🪦 Unknown Chatter — 0\n"
                "🌲 New Chatter — 25\n"
                "🥉 Chatter — 100\n"
                "🥈 Regular Chatter — 250\n"
                "🏅 Frequent Chatter — 500\n"
                "💫 Dedicated Chatter — 1,000\n"
                "✨ Devoted Chatter — 2,500\n"
                "⭐ Ultimate Chatter — 5,000\n"
                "🌟 No Life Chatter — 10,000\n"
                "👑 The Chosen Chatter — 50,000\n"
                "☄️ The Chat God — 100,000\n"
                "<:refense:1526107149338411069> True Refense — 1,000,000"
            )

        # ---------------- PAGE 3 ----------------

        elif self.page == 3:

            embed.description = (
                "**☠️ Dangerous Message Achievements**\n\n"
                "Awarded based on your single most dangerous message.\n\n"
                "🚨 Alarming Message — 1.0+\n"
                "😭 Terrible Message — 1.5+\n"
                "🤮 Vile Message — 2.0+\n"
                "😵 Atrocious Message — 2.5+\n"
                "☠️ Abhorrent Message — 3.0+"
            )

        # ---------------- PAGE 4 ----------------

        elif self.page == 4:

            embed.description = (
                "**🗳️ Voting Achievements**\n\n"
                "Earned by voting for RefenseBot on Top.gg.\n\n"
                "✉️ Voter — 1\n"
                "📨 Regular Voter — 3\n"
                "📝 Frequent Voter — 5\n"
                "🗳️ Epic Voter — 10\n"
                "💌 Super Voter — 25\n"
                "🔥 Legendary Voter — 50\n"
                "❤️‍🔥 Ultimate Voter — 100"
            )

        # ---------------- PAGE 5 ----------------

        elif self.page == 5:

            embed.description = (
                "**💥 Vote Spending Achievements**\n\n"
                "Spend votes to permanently remove dangerous messages from your history.\n\n"
                "❌ Message Remover — 1\n"
                "⚠️ Message Executor — 3\n"
                "🧨 Danger Evader — 5\n"
                "💣 Danger Demolisher — 10\n"
                "💥 History Eradicator — 25\n"
                "🤯 The Past's Pulveriser — 50"
            )

        embed.set_footer(
            text=f"Page {self.page + 1}/{self.max_pages}"
        )

        return embed

    @discord.ui.button(
        emoji="⬅️",
        style=discord.ButtonStyle.secondary
    )
    async def left(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page -= 1
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    @discord.ui.button(
        emoji="➡️",
        style=discord.ButtonStyle.secondary
    )
    async def right(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page += 1
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True