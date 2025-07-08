# cogs/devtools.py
from discord.ext import commands
import discord




class DevTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildjackid = 875349586141675582
        self.guildobject = discord.Object(id=self.guildjackid) 
        self.moeidnum = 98200277580009472
#    @commands.is_owner()
#    @commands.command(name="reload")
#    async def reload_cog(self, ctx, cog: str):
#        """
#        Usage:   !reload model
#        Reloads cogs/model.py
#        """
#        module = f"cogs.{cog}"
#        try:
#            self.bot.reload_extension(module)
#            await ctx.send(f"✅ Reloaded **{module}**")
#        except commands.ExtensionError as e:
#            await ctx.send(f"❌ Failed to reload **{module}**:\n```\n{e}\n```")
#
#    @commands.is_owner()
#    @commands.command(name="sync2")
#    async def sync2(self, interaction):
#        
#        if not self.bot.get_user(98200277580009472):
#            return
#
#        #self.add_command(ping2)
#        print(f"App commands registered in tree: {[cmd.name for cmd in self.tree.get_commands()]}")
#
#        # remove stale commands
#        self.tree.clear_commands(guild=self.guildobject)
#        print("✅ Cleared guild commands.")
#
#        # Sync global commands (commands without @guilds)
#        synced_global = await self.tree.sync()
#        print(f"✅ {len(synced_global)} commands synced globally 🌍.")
#
#        # Sync guild commands (commands with @guilds)
#        synced_in_guild = await self.tree.sync(guild=self.guildobject)
#        print(f"✅ {len(synced_in_guild)} commands synced to guild {self.guildobject.id}.")



    @commands.Cog.listener("on_message")
    async def devtoolslistener(self, message):
        if message.author.bot:
            return  # Ignore bot messages

        if message.content.startswith('sync commands plz') and (message.author.id == self.moeidnum):
            #self.add_command(ping2)
            print(f"App commands registered in tree: {[cmd.name for cmd in self.bot.tree.get_commands()]}")


            self.bot.tree.copy_global_to(guild=self.guildobject)
            synced = await self.bot.tree.sync(guild=self.guildobject)
            print(f"Synced {len(synced)} command(s) to the test guild.")
#            # remove stale commands
#            self.bot.tree.clear_commands(guild=self.guildobject)
#            print("✅ Cleared guild commands.")
#
#            # Sync global commands (commands without @guilds)
#            synced_global = await self.bot.tree.sync()
#            print(f"✅ {len(synced_global)} commands synced globally 🌍.")
#
#            # Sync guild commands (commands with @guilds)
#            synced_in_guild = await self.bot.tree.sync(guild=self.guildobject)
#            print(f"✅ {len(synced_in_guild)} commands synced to guild {self.guildobject.id}.")

        if message.content.startswith('sync clear plz') and (message.author.id == self.moeidnum):
            # remove stale commands
            self.bot.tree.clear_commands(guild=None)
            self.bot.tree.clear_commands(guild=self.guildobject)
            print("✅ Cleared global and guild commands.")




async def setup(bot):
    await bot.add_cog(DevTools(bot))