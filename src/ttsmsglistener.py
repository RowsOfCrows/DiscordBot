import discord
from discord.ext import commands
from discord import app_commands

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
import wave
import tempfile
from piper import PiperVoice
import json

from src.botfilepaths import BOTDATA_DIR, LOCALDATA_DIR


BD_PIPERVOICES  = os.path.join(BOTDATA_DIR, "pipervoices")
LD_TEMPTTS  = os.path.join(LOCALDATA_DIR, "temptts")
#LD_USERDATA = os.path.join(LOCALDATA_DIR, "UserData")
user_tts_settings = os.path.join(LOCALDATA_DIR, "UserData", "tts_user_settings.json")


@dataclass
class VoiceInfo:
    name: str
    file: str

class PiperVoices(Enum):
    HFC_MALE              = (f"{BD_PIPERVOICES}/en_US-hfc_male-medium.onnx")
    LESSAC                = (f"{BD_PIPERVOICES}/en_US-lessac-high.onnx")
    NORTHERN_ENGLISH_MALE = (f"{BD_PIPERVOICES}/en_GB-northern_english_male-medium.onnx")
    ARTUR_SL              = (f"{BD_PIPERVOICES}/sl_SI-artur-medium.onnx")
    #  more voices soon maybe idk idc there's a list at the bottom to download if I wanted

    # What piper needs
    def load(self) -> PiperVoice:
        return PiperVoice.load(self.value)

    # What users see in menus/UI
    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ").title()
        # HFC_MALE -> "Hfc Male", LESSAC -> "Lessac", etc.

    # What goes in JSON
    def to_json(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, name: str) -> "PiperVoices":
        return cls[name]


TTS_VOICE_DEFAULTS = {
    "tts_enabled": False,
    "voice": PiperVoices.HFC_MALE.name,
    "length_scale": 1.0, # higher is slower, lower is faster
    "noise_scale": 0.667, # audio variation
    "noise_w_scale": 0.8, # speaking variation
    "normalize_audio": False, # use raw audio from voice
}

BOUNDS = {
    "length_scale":  (0.5, 2.0),
    "noise_scale":   (0.0, 1.0),
    "noise_w_scale": (0.0, 1.0),
}

def load_settings() -> dict:
    if not os.path.exists(user_tts_settings):
        return {}
    with open(user_tts_settings, "r") as f:
        return json.load(f)
    
def save_settings(data: dict) -> None:
    with open(user_tts_settings, "w") as f:
        json.dump(data, f, indent=2)

def get_user_settings(user_id: int) -> dict:
    """Returns the user's settings, filling in any missing keys with defaults."""
    data = load_settings()
    user = data.get(str(user_id), {})
    return {**TTS_VOICE_DEFAULTS, **user}  # defaults are overwritten by whatever the user has saved

def update_user_settings(user_id: int, **kwargs) -> dict:
    """
    Updates only the keys passed in kwargs.
    Returns a dict of any validation errors so the caller can report them.
    """
    errors = {}

    for key, value in kwargs.items():
        if key in BOUNDS and value is not None:
            low, high = BOUNDS[key]
            if not (low <= value <= high):
                errors[key] = f"must be between {low} and {high}"

    if errors:
        return errors  # don't save anything if there are validation problems

    data = load_settings()
    user_key = str(user_id)

    if user_key not in data:
        data[user_key] = {}

    for key, value in kwargs.items():
        if value is not None:
            data[user_key][key] = value

    save_settings(data)
    return {}  # empty dict means no errors



class TTSListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.disconnect_task = None 
        self._voice_cache: dict[PiperVoices, PiperVoice] = {}
        self._queues: dict[int, asyncio.Queue] = {}       # guild_id -> Queue
        self._workers: dict[int, asyncio.Task] = {}       # guild_id -> worker Task
        self._now_playing: dict[int, int] = {}  # guild_id -> user_id

    def _get_queue(self, guild_id: int) -> asyncio.Queue:
        if guild_id not in self._queues:
            self._queues[guild_id] = asyncio.Queue()
        return self._queues[guild_id]
    
    async def _queue_worker(self, guild: discord.Guild):
        queue = self._get_queue(guild.id)
        loop = asyncio.get_event_loop()
        while True:
            wav_path, voice_channel, user_id = await queue.get()

            bot_vc = guild.voice_client
            if bot_vc is None:
                bot_vc = await voice_channel.connect(reconnect=True)
                await asyncio.sleep(1)
            elif bot_vc.channel != voice_channel:
                await bot_vc.move_to(voice_channel)

            if self.disconnect_task:
                self.disconnect_task.cancel()
            self.disconnect_task = asyncio.create_task(self._auto_disconnect(guild))

            self._now_playing[guild.id] = user_id  # set before playing
            done = loop.create_future()

            def after_playing(error):
                print(f"Finished playing TTS: {wav_path}")
                try:
                    os.remove(wav_path)
                except FileNotFoundError:
                    pass
                if error:
                    print(f"TTS playback error: {error}")
                self._now_playing.pop(guild.id, None)  # clear when done
                loop.call_soon_threadsafe(done.set_result, None)

            bot_vc.play(discord.FFmpegPCMAudio(wav_path), after=after_playing)
            await done
            queue.task_done()

    async def make_wav(self, text: str, piper_voice: PiperVoices):
        os.makedirs(LD_TEMPTTS, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=LD_TEMPTTS) as tmp:
            tmp_path = tmp.name

        if piper_voice not in self._voice_cache:
            self._voice_cache[piper_voice] = piper_voice.load()
        loaded_voice = self._voice_cache[piper_voice]

        with wave.open(tmp_path, "wb") as wav_file:
            loaded_voice.synthesize_wav(text, wav_file)

        return os.path.relpath(tmp_path)

    async def _auto_disconnect(self, guild, delay=True):
        if delay:
            await asyncio.sleep(900)
        vc = guild.voice_client
        if vc:
            if vc.is_playing():
                vc.stop()
            await vc.disconnect()

        # Drain the queue so the worker doesn't try to play files we're about to delete
        queue = self._get_queue(guild.id)
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break

        for f in os.listdir(LD_TEMPTTS):
            os.remove(os.path.join(LD_TEMPTTS, f))


    @app_commands.command (name="ttsconfig", description="Reads your messages outloud in voice channels.") #just type in any channel in the server to speak. You can also set your preferred voice here.
    @app_commands.describe(voice="What do you want to sound like?",
                           tts_enabled="Read your messages outloud from any channel",
                           length_scale="Speaking speed (0.5 = fast, 2.0 = slow)",
                           noise_scale="Audio variation (0.0 to 1.0)",
                           noise_w_scale="Speaking variation (0.0 to 1.0)",
                           normalize_audio="Use raw audio",)
    @app_commands.choices (voice=[app_commands.Choice(name=v.display_name, value=v.name) for v in PiperVoices],)
    async def ttsconfig(self, interaction: discord.Interaction,
                        tts_enabled: bool | None = None, 
                        voice: app_commands.Choice[str] | None = None,
                        length_scale: float | None = None,
                        noise_scale: float | None = None,
                        noise_w_scale: float | None = None,
                        normalize_audio: bool | None = None,
                        ):
        await interaction.response.defer()  # Optional: useful if searching takes time

        errors = update_user_settings(
            interaction.user.id,
            tts_enabled=tts_enabled,
            voice=voice.value if voice else None,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_w_scale=noise_w_scale,
            normalize_audio=normalize_audio
        )
        if errors:
            error_lines = "\n".join(f"**{k}**: {v}" for k, v in errors.items())
            await interaction.followup.send(f"❌ Couldn't save settings ❌\n⚠️ {error_lines}")
            return

        # Show them their full current settings after saving
        current = get_user_settings(interaction.user.id)
        await interaction.followup.send(
            f"✅ Settings saved! Your current config:\n"
            f"```ansi\n"
            f"TTS Enabled:     {current['tts_enabled']}\n"
            f"Voice:           {current['voice']}\n"
            f"Length scale:    {current['length_scale']}\n"
            f"Noise scale:     {current['noise_scale']}\n"
            f"Noise W scale:   {current['noise_w_scale']}\n"
            f"Normalize audio: {current['normalize_audio']}\n"
            f"```"
        )

    @app_commands.command(name="ttsadmintoggle", description="Admin: toggle TTS for a user.")
    @app_commands.describe(user="The user to modify", tts_enabled="Enable or disable their TTS")
    @app_commands.checks.has_permissions(administrator=True)
    async def ttsadmin(self, interaction: discord.Interaction,
                    user: discord.Member,
                    tts_enabled: bool):
        is_admin = interaction.user.guild_permissions.administrator
        if not is_admin:
            print()
        update_user_settings(user.id, tts_enabled=tts_enabled)
        status = "enabled" if tts_enabled else "disabled"
        current = get_user_settings(user.id)

        await interaction.response.send_message(
            f"✅ TTS **{status}** for {user.display_name}."
            #f""
            #f"```ansi\n"
            #f"TTS enabled:     {current['tts_enabled']}\n"
            #f"Voice:           {current['voice']}\n"
            #f"Length scale:    {current['length_scale']}\n"
            #f"Noise scale:     {current['noise_scale']}\n"
            #f"Noise W scale:   {current['noise_w_scale']}\n"
            #f"Normalize audio: {current['normalize_audio']}\n"
            #f"```"
            , ephemeral=not is_admin
        )

    @app_commands.command(name="ttsskip", description="Skip the currently playing TTS message.")
    async def ttsskip(self, interaction: discord.Interaction):
        now_playing_id = self._now_playing.get(interaction.guild.id)
        member = interaction.guild.get_member(now_playing_id)
        name = member.display_name if member else str(now_playing_id)
        print(f" [SKIP REQUEST] {interaction.user.display_name} - Now playing user:{name} - Admin:{interaction.user.guild_permissions.administrator}")
        
        vc = interaction.guild.voice_client
        if vc is None or not vc.is_playing():
            await interaction.response.send_message("Nothing is playing right now. 😴", ephemeral=True)
            return

        now_playing_id = self._now_playing.get(interaction.guild.id)
        is_admin = interaction.user.guild_permissions.administrator

        if not is_admin and interaction.user.id != now_playing_id:
            await interaction.response.send_message("You can only skip your own messages.")
            return

        vc.stop()
        await interaction.response.send_message("⏭️ Skipped.")

    @commands.Cog.listener("on_message")
    async def on_message_ttsfm(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content.startswith("!ttsdc"):
            asyncio.create_task(self._auto_disconnect(message.guild, delay=False))
            return
        if not message.author.voice or not message.author.voice.channel: # make sure user is in a voice channel 
            return
        if not message.content or not message.content.strip(): # if the message is empty or just whitespace, ignore it. can happen with pictures
            return

        user_settings = get_user_settings(message.author.id)
        if not user_settings["tts_enabled"]:
            return

        try:
            piper_voice = PiperVoices.from_json(user_settings["voice"])
        except KeyError:
            print(f"Unknown voice '{user_settings['voice']}' for user, skipping.")
            return

        wav_path = await self.make_wav(message.content, piper_voice)
        voice_channel = message.author.voice.channel

        queue = self._get_queue(message.guild.id)
        await queue.put((wav_path, voice_channel, message.author.id))

        # Start a worker for this guild if one isn't already running
        worker = self._workers.get(message.guild.id)
        if worker is None or worker.done():
            self._workers[message.guild.id] = asyncio.create_task(
                self._queue_worker(message.guild)
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        vc = member.guild.voice_client
        if vc is None:
            return

        # Check if the bot's channel is now empty of humans
        humans = [m for m in vc.channel.members if not m.bot]
        if len(humans) == 0:
            await self._auto_disconnect(member.guild, delay=False)

async def setup(bot):
    await bot.add_cog(TTSListener(bot))


    
""" 
for list:     python3 -m piper.download_voices 
for download: python3 -m piper.download_voices en_US-lessac-medium
https://rhasspy.github.io/piper-samples/#en_US-amy-medium
"""