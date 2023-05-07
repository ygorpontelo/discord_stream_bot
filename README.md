# Discord Stream Bot

Once you configure your own personal bot, [see tutorial here](https://discordpy.readthedocs.io/en/stable/discord.html), place the token in a txt file in the same folder called token.txt.

This bot uses Pyaudio to read any available input and stream the audio to discord. Only mono and stereo inputs are supported (1 and 2 channels). The script will present a nice CLI interface to select those.

This bot does not create a device input, only reads available ones. If you want to redirect audio using virtual inputs, you need an interface to do that, like [Jack audio](https://jackaudio.org/) on Linux or [VB-Cable](https://vb-audio.com/Cable/) on Windows.

Poetry is the recommended way to manage dependencies, but you can install them via pip normally with requirements.txt (includes all dependencies).

To compile the bot to exe, use this command:

```
pyinstaller --console --onefile --collect-all discord --collect-all samplerate --collect-all pyaudio bot.py
```
