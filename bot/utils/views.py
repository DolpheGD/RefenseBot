import discord

from bot.utils.embedder import get_danger_color

class LeaderboardView(discord.ui.View):
    def __init__(self, users, server_name):
        super().__init__(timeout=300)
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