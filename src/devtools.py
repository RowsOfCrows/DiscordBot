from discord.ext import commands
import discord
import asyncio

class DevTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildjackid = 875349586141675582
        self.guildobject = discord.Object(id=self.guildjackid) 
        self.moeidnum = 98200277580009472
        self.ruseidnm = 927067777582391327

        self.guildobjecthayded = discord.Object(id=1183219541350817822) 

    @commands.Cog.listener("on_message")
    async def devtoolslistener(self, message):
        if message.author.bot:
            return 
        if message.author.id != self.moeidnum:
            return
        
        if message.content.startswith('sync commands plz'):
            print(f"App commands registered in tree: {[cmd.name for cmd in self.bot.tree.get_commands()]}")

            self.bot.tree.copy_global_to(guild=self.guildobject)
            synced = await self.bot.tree.sync(guild=self.guildobject)
            print(f"Synced {len(synced)} command(s) to the test guild.")

        if message.content.startswith('sync clear plz'):
            self.bot.tree.clear_commands(guild=self.guildobject)
            print("✅ Cleared guild commands.")
        

        if message.content.startswith('synclist'):
            # synclist <guild_id>
            # synclist 
            parts = message.content.split()
            if len(parts) > 1:  
                guild = discord.Object(id=int(parts[1]))
                cmds = await self.bot.tree.fetch_commands(guild=guild)
                print(f"{[cmd.name for cmd in cmds]}")
            else: 
                global_cmds = await self.bot.tree.fetch_commands(guild=message.guild)
                print(f"Global: {[cmd.name for cmd in global_cmds]}")
        

        if message.content.startswith('!sync'):
            # sync <guild_id> clear
            # sync <guild_id>
            
            parts = message.content.split()
            if len(parts) < 2:
                return
            
            try:
                guild_id = int(parts[1])
            except ValueError:
                await message.channel.send("invalid guild id")
                return
            
            guild = discord.Object(id=guild_id)
            action = parts[2] if len(parts) > 2 else "sync"

            if action == "clear":
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
                await message.channel.send(f"✅ Cleared commands for guild {guild_id}")
            elif action == "sync":
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
                print(f"App commands registered in tree: {[cmd.name for cmd in self.bot.tree.get_commands()]}")
                await message.channel.send(f"✅ Synced {len(synced)} command(s) to guild {guild_id}")
            else:
                return


async def setup(bot):
    await bot.add_cog(DevTools(bot))