import sys
import discord
import pyaudio
import samplerate
import questionary
import numpy as np

from discord.ext import commands


class PyAudioPCM(discord.AudioSource):

    def __init__(self, device, audio) -> None:
        super().__init__()
        self.d = device
        self.ratio = 48000/self.d["defaultSampleRate"]
        self.channels = self.d["maxInputChannels"]
        self.chunk = int(self.d["defaultSampleRate"] * 0.02)
        self.stream = audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=int(self.d["defaultSampleRate"]),
            input=True,
            input_device_index=self.d["index"],
            frames_per_buffer=self.chunk,
        )
        self.resampler = None
        if self.ratio != 1:
            self.resampler = samplerate.Resampler("sinc_best", channels=2)

    def read(self) -> bytes:
        frame = self.stream.read(self.chunk, exception_on_overflow=False)
        frame = np.frombuffer(frame, dtype=np.int16)
        if self.channels == 1:
            frame = np.repeat(frame, 2)
        if self.resampler:
            frame = np.stack((frame[::2], frame[1::2]) , axis=1)
            return self.resampler.process(frame, self.ratio).astype(np.int16).tobytes()
        return frame.tobytes()


def create_bot(device, audio) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", description="Discord Audio Stream Bot", intents=intents)

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

    @bot.command(name="join", aliases=["j"], help="Join user channel")
    async def join(ctx):
        """Joins a voice channel"""

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
    
    @bot.command(name="play", aliases=["p"], help="Play audio")
    async def play(ctx):
        """Streams sound from audio device"""

        async with ctx.typing():
            ctx.voice_client.play(PyAudioPCM(device, audio), after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Streaming From {device["name"]}')
    
    @bot.command(name="volume", aliases=["v"], help="Change bot volume")
    async def volume(ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")
    
    @bot.command(name="stop", aliases=["s"], help="Disconnect bot")
    async def stop(ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()
    
    @play.before_invoke
    async def ensure_voice(ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
    
    return bot


if __name__ == "__main__":
    try:
        with open("token.txt", 'r') as f:
            token = f.readline()
    except FileNotFoundError:
        print("Token file not found!")
        input("Press Enter to exit")
        sys.exit(1)

    p = pyaudio.PyAudio()

    # get all available inputs, mono or stereo, with all possible drivers
    # some of those do not work, test it to check
    device_inputs, index = {}, 1
    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if 0 < d["maxInputChannels"] < 3:
            api = p.get_host_api_info_by_index(d["hostApi"])["name"]
            name = f'{index} - Device: {d["name"]}, Channels: {d["maxInputChannels"]}, API: {api}'
            device_inputs[name] = d
            index += 1

    # choice of input by user
    answer = questionary.select(
        "Select Device you want to stream:",
        choices=list(device_inputs),
    ).ask()

    # start bot
    create_bot(device_inputs[answer], p).run(token)
