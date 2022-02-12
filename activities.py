import nextcord
from nextcord.ext import commands

import random

COMMAND_PREFIX = "!"

taylor_swift_albums = [
    'Taylor Swift',
    'Speak Now',
    '1989',
    'reputation',
    'Lover',
    'Folklore',
    'Evermore',
    "Fearless (Taylor's Version)",
    "Red (Taylor's Version)",
]

activities_choices = [
    nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{COMMAND_PREFIX}help"),
    nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{random.choice(taylor_swift_albums)}")
]