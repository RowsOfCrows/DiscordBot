# cogs/devtools.py
from discord.ext import commands

class DevTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="reload")
    async def reload_cog(self, ctx, cog: str):
        """
        Usage:   !reload model
        Reloads cogs/model.py
        """
        module = f"cogs.{cog}"
        try:
            self.bot.reload_extension(module)
            await ctx.send(f"✅ Reloaded **{module}**")
        except commands.ExtensionError as e:
            await ctx.send(f"❌ Failed to reload **{module}**:\n```\n{e}\n```")

async def setup(bot):
    await bot.add_cog(DevTools(bot))