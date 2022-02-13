[Boombox Icon]('https://raw.githubusercontent.com/lonewanderer27/Boombox-v3/master/boombox_icon.png') # Boombox v3

### Background
It was August 27 2021 when Groovy was issued a cease and desist order for violating Youtube EULA. My friends and I became worried that we wouldn't be able to play music in Discord anymore. So I set out to build a temporary music bot by watching this [simple bot tutorial by Max Codez](https://www.youtube.com/watch?v=jHZlvRr9KxM&t=131s), that's when Boombox v1 was born.

Fast forward of 2 weeks, I followed [freeCodeCamp's JS Bot Tutorial](https://www.freecodecamp.org/news/create-a-discord-bot-with-javascript-nodejs/), I was able to add queue functionality and to show what's currently playing and this is Boombox v2. However I was still discontented as this version is written in Javascript, which I am totally alien of at that time... meaning I am not able to expand the Boombox functionalities if I wanted to.

So I decided that in the following months, I will learn Python till the point that I'm able to make the version 3 of Boombox. I followed [Dr. Angela Yu's 100 Days of Code course](https://www.udemy.com/course/100-days-of-code/) and... *<sub>ps. I wasn't able to complete the 100 Days, I only got to 20th Day 😂</sub>* 

But despite that I was able to build a lot of projects using only those 20 days of knowledge, it started out with a [Comment Web-App](https://github.com/lonewanderer27/jammacomments), and then an [E-Commerce Website](https://github.com/lonewanderer27/JAMMA) plus all of the various exercises that Dr. Yu made me do.

And now here we are, after 6 months of learning Python, Boombox v3 is finally alive.

# Features!
- Play a Youtube video or link
- Pause / Play music
- Display the currently playing music
- Queue system
- Change it's prefix 

### Planned:
- [ ] Allow the user to reorder queued music
- [ ] Play Spotify links
- [ ] Use slash commands

# Deploy the Bot!

You can host Boombox in either Replit or Heroku. 
Make sure to setup a bot in [Discord Developers](https://discord.com/developers/applications) first, then enable the following options:
- PRESENCE INTENT
- SERVER MEMBERS INTENT
- MESSAGE CONTENT INTENT 

Then at last get the Token.

## DEPLOY TO REPLIT

### What You'll Need:
1. Discord Developer Account & Bot
2. Replit REPL
3. Firebase Realtime DB
4. Patience 😉

### Setup Firebase:
1. Go to [Firebase](https://firebase.google.com/) and register if you don't have an account yet.
2. Create a Project and then enable Realtime Database on that. *<sub>Make sure to choose Locked Down mode for security!</sub>*
3. Go to Project Settings -> Service Accounts.
4. Enable Service Account and then click `Generate new private key`.
5. Go to your Realtime Database again and copy the Database link.
6. Open your downloaded JSON service account and append the following:
	- Realtime Database link	*<sub>inside of `firebase_database_url` key</sub>* 
	- Your Discord Bot Token		*<sub>inside of  `BOOMBOX_V3_TOKEN` key</sub>*

### Setup Replit:
1. Go to [Replit](https://replit.com/) and register if you don't have an account yet.
2. Create a new repl by clicking the `+` button at the top right.
3. Click `Import From GitHub`, copy the link of this repo to the URL textbox, then click the `Import From GitHub` at the bottom right.
4. Put `python3 app.py` for the repl run command then click enter.
5. Open the sidebar and then go to Secrets.
6. Click `Open RAW Editor`, copy all the contents of the service account JSON that you downloaded earlier, then hit save.
7. Go back to Files, delete the `requirements.txt` then manually install these packages: 
	- PyNaCl
	- nextcord
8. Finally hit `Run` to install the remaining dependencies, you should see the bot running by looking at the logs.

## HEROKU
Coming soon...
	