import discord
from discord.ext import commands
from discord.utils import find
from __main__ import send_cmd_help
import json, re, sys, urllib.request, urllib.parse, urllib.error
import codecs
import requests
import random
import os
from urllib.request import urlopen
from .utils.dataIO import dataIO, fileIO
from wand.image import Image
from wand.display import display
from wand.drawing import Drawing
from wand.color import Color
from cogs.utils import checks

bgs = {
    'blue_triangles':'http://puu.sh/pUeKt/bd02db94a1.jpg',
    'rainbow_circles': 'http://puu.sh/pUdMe/4cdc33ed08.jpg',
    'blue_triangles_2': 'http://puu.sh/pVjqw/06b6b6395f.jpg',
    'blue_triangles_3': 'http://puu.sh/pUdJb/47220936c9.jpg',
    'purple_orange_pentagons': 'http://puu.sh/pUdBf/8959a98929.png',
    'red_white_triangles': 'http://puu.sh/pUdyQ/62eee8b326.jpg',
    'purple_pink_triangles': 'http://puu.sh/pSSFN/34704f54e7.jpg,',
    'waterfall': 'http://puu.sh/pSSHJ/20fd045df0.jpg',
    'pink_triangles': 'http://puu.sh/pST3z/238863993a.png',
    'rainbow_triangles': 'http://puu.sh/pST4a/563337774d.jpg',
    'blue_green_triangles': 'http://puu.sh/pWfYt/f3099aa970.jpg',
    'random': 'A random bg from this list'
}

help_msg = [
            "That player either doesn't exist in the database, hasn't played enough, or you don't have an osu api key (*it's required*). You can get one from https://osu.ppy.sh/p/api. If already have a key, do **<p>osuset key** to set your key",
            "It doesn't seem that you have an account linked. Do **<p>osuset user**.",
            "It doesn't seem that the discord user has an account linked."
            ]

class Osu:
    """Cog to give osu! stats for all gamemodes."""

    def __init__(self, bot):
        self.bot = bot
        self.osu_api_key = fileIO("data/osu/apikey.json", "load")

    @commands.group(pass_context=True)
    async def osuset(self, ctx):
        """Where you can define some settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return 

    @osuset.command(pass_context=True)
    @checks.is_owner()
    async def key(self, ctx):
        """Sets your osu api key"""
        await self.bot.whisper("Type your osu! api key. You can reply here.")
        key = await self.bot.wait_for_message(timeout=30,
                                                   author=ctx.message.author)
        if key is None:
            return
        else:
            self.osu_api_key["osu_api_key"] = key.content
            fileIO("data/osu/apikey.json", "save", self.osu_api_key)
            await self.bot.whisper("API Key details added.")

    @commands.command(pass_context=True, no_pm=True)
    async def osu(self, ctx, *, username= None):
        """Gives osu! standard user stats"""
        await self.process_user_small(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def taiko(self, ctx, *, username=None):
        """Gives taiko user stats"""
        await self.process_user_small(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def ctb(self, ctx, *, username=None):
        """Gives Catch the Beat user stats"""
        await self.process_user_small(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def mania(self, ctx, *, username=None):
        """Gives osu standard user stats"""
        await self.process_user_small(ctx, username, 3)

    @commands.command(pass_context=True, no_pm=True)
    async def osutop(self, ctx, *, username=None):
        """Gives osu! standard user best plays"""
        await self.process_user_profile(ctx, username, 0)

    @commands.command(pass_context=True, no_pm=True)
    async def taikotop(self, ctx, *, username=None):
        """Gives taiko user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 1)

    @commands.command(pass_context=True, no_pm=True)
    async def ctbtop(self, ctx, *, username=None):
        """Gives ctb user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 2)

    @commands.command(pass_context=True, no_pm=True)
    async def maniatop(self, ctx, *, username=None):
        """Gives osu! mania user stats and best plays"""
        key = self.osu_api_key["osu_api_key"]
        await self.process_user_profile(ctx, username, 3)

    @osuset.command(pass_context=True, no_pm=True)
    async def listbgs(self, ctx):
        """Ugly list of available backgrounds. Will fix."""
        await self.bot.say("Here is a list of the current available backgrounds:\n")
        bg_list = "```"
        for background in bgs.keys():
            bg_list += "{:>24}  <{:>24}> \n".format(background, bgs[background])
        bg_list += "```"
        await self.bot.say(bg_list)
        await self.bot.say("If you would like to set a default background, do **<p>osuset bg**".format(list(bgs.keys())))

    @osuset.command(pass_context=True, no_pm=True)
    async def user(self, ctx, *, username):
        """Sets user information given an osu! username"""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        if user.server.id not in self.user_settings:
            self.user_settings[user.server.id] = {}

        if not self.check_user_exists(user):
            try:
                osu_user = json.loads(get_user(key, username, 1).decode("utf-8"))
                newuser = {
                    "discord_username": user.name, 
                    "osu_username": username,
                    "osu_user_id": osu_user[0]["user_id"],
                    "default_gamemode": 0,
                    "background": ""
                }

                self.user_settings[server.id][user.id] = newuser
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your account has been linked to osu! username `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
        else:
            try:
                osu_user = json.loads(get_user(key, username, 1).decode("utf-8"))
                self.user_settings[server.id][user.id]["osu_username"] = username
                self.user_settings[server.id][user.id]["osu_user_id"] = osu_user[0]["user_id"]
                fileIO('data/osu/user_settings.json', "save", self.user_settings)
                await self.bot.say("{}, your osu! username has been edited to `{}`".format(user.mention, osu_user[0]["username"]))
            except:
                await self.bot.say("{} doesn't exist in the osu! database.".format(username))
                         
    @osuset.command(pass_context=True, no_pm=True)
    async def bg(self, ctx, background_name):
        """Sets user background"""
        user = ctx.message.author
        server = user.server
        channel = ctx.message.channel

        if self.check_user_exists(user):
            if background_name in bgs.keys():
                self.user_settings[server.id][user.id]["background"] = background_name
                await self.bot.say("{}, your default background is now: `{}`".format(user.mention, background_name))            
            else:
                await self.bot.say("That is not a valid background. Do **<p>osuset listbgs** to view a list.")          
        else:
            await self.bot.say(help_msg[1])  

    # Gets json information to proccess the small version of the image
    async def process_user_small(self, ctx, username, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server

        if await self.process_username(ctx, username):
            username = await self.process_username(ctx, username)
        else:
            return

        try: 
            userinfo = get_user(key, username, gamemode).decode("utf-8")
            if (len(json.loads(userinfo)) > 0):

                if self.check_user_exists(user):
                    if username == self.user_settings[server.id][user.id]["osu_username"]:
                        self.draw_user_small(json.loads(userinfo)[0], gamemode, self.user_settings[server.id][user.id]["background"])
                    else:
                        self.draw_user_small(json.loads(userinfo)[0], gamemode, "") # random background
                else:
                    self.draw_user_small(json.loads(userinfo)[0], gamemode, "") # random background
                
                await self.bot.send_typing(channel)            
                await self.bot.send_file(channel, 'data/osu/user.png')
            else:
                await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg[0])

    # Gets json information to proccess the top play version of the image
    async def process_user_profile(self, ctx, username, gamemode: int):
        key = self.osu_api_key["osu_api_key"]
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server
        num_best_plays = 3

        if await self.process_username(ctx, username):
            username = await self.process_username(ctx, username)
        else:
            return

        try:
            # get userinfo
            userinfo = get_user(key, username, gamemode).decode("utf-8")
            userbest = get_user_best(key, username, gamemode, num_best_plays).decode("utf-8")

            if (len(json.loads(userinfo)) > 0):
                if self.check_user_exists(user):
                    if username == self.user_settings[server.id][user.id]["osu_username"]:
                        self.draw_user_profile(json.loads(userinfo)[0],json.loads(userbest), gamemode, self.user_settings[server.id][user.id]["background"]) # only takes the first one
                    else:
                        self.draw_user_profile(json.loads(userinfo)[0],json.loads(userbest), gamemode, "") # random background                            
                else:
                    self.draw_user_profile(json.loads(userinfo)[0],json.loads(userbest), gamemode, "") # random background                            
                await self.bot.send_typing(channel)
                await self.bot.send_file(channel, 'data/osu/user_profile.png')
            else:
                await self.bot.say("Player not found :cry:")
        except:
            await self.bot.say(help_msg[0])

    ## processes username. probably the worst chunck of code in this project so far. will fix/clean later
    async def process_username(self, ctx, username):
        channel = ctx.message.channel
        user = ctx.message.author
        server = user.server
        key = self.osu_api_key["osu_api_key"]

        # if nothing is given, must rely on if there's account
        if not username:
            if self.check_user_exists(user):
                username = self.user_settings[server.id][user.id]["osu_username"]
            else:
                await self.bot.say("It doesn't seem that you have an account linked. Do **<p>osuset user**.")
                return # bad practice, but too lazy to make it nice
        # if it's a discord user, first check to see if they are in database and choose that username
        # then see if the discord username is a osu username, then try the string itself
        elif find(lambda m: m.name == username, channel.server.members) is not None:
            target = find(lambda m: m.name == username, channel.server.members)
            try:
                self.check_user_exists(target)
                username = self.user_settings[server.id][target.id]["osu_username"]
            except:
                if json.loads(get_user(key, username, 0).decode("utf-8")):
                    username = str(target)
                else:
                    await self.bot.say(help_msg[2])
                    return
        # @ implies its a discord user (if not, it will just say user not found in the next section)
        # if not found, then oh well.
        elif "@" in username:   
            user_id = username.replace("@", "").replace("<","").replace(">","")
            try:
                if self.user_settings[server.id][user_id]:
                    username = self.user_settings[server.id][user_id]["osu_username"]
            except:
                await self.bot.say(help_msg[2])
                return
        else:
            username = str(username)
        return username

    # Checks if user exists
    def check_user_exists(self, user):
        if user.server.id not in self.user_settings:
            self.user_settings[user.server.id] = {}

        if user.id not in self.user_settings[user.server.id]:
            return False
        return True

    # Gives a small user profile image
    def draw_user_small(self, user, gamemode: int, background:str):
        font = 'Tahoma'

        # checks if user has stored background
        if background in bgs.keys() and background != 'random':
            bg_url = bgs[background]
        else:
            bg_url = random.choice(list(bgs.values()))  

        bg_req = urllib.request.Request(bg_url, headers={'User-Agent': 'Mozilla/5.0'})
        bg = urlopen(bg_req)
        with Image(file=bg) as base_img:
            # background cropping as base image
            base_img.resize(600,600)
            base_img.crop(0,0,488,170)

            # draw transparent black rectangle
            with Drawing() as draw:
                draw.fill_color = Color('#000000')
                draw.fill_opacity = 0.6
                draw.rectangle(left=10,top=10,right=478,bottom=160)
                draw(base_img)

            # create level graphic
            with Drawing() as draw:
                level_int = int(float(user['level']))
                level_percent = float(user['level']) - level_int
                full_length = 458
                level_length = full_length * level_percent
                draw.fill_color = Color('#FFF')
                draw.fill_opacity = 0.6
                draw.rectangle(left=15,top=145, width=level_length, bottom=155)
                draw(base_img)
            with Drawing() as draw:
                draw.fill_opacity = 1
                draw.text_alignment = 'center'
                draw.font_size = 13
                draw.font_weight = 500
                draw.fill_color = Color('#FFF')
                draw.text(int(base_img.width/2), 155, "Lvl {}".format(str(level_int)))
                draw(base_img)

            # grab user profile image
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
            profile_req = urllib.request.Request(profile_url, headers={'User-Agent': 'Mozilla/5.0'})
            profile = urlopen(profile_req)
            with Image(file=profile) as profile_img:
                # user_profile image resizing
                profile_img.resize(130,130)     
                base_img.composite(profile_img, left=10, top=10)
            profile.close()

            # writes lables
            with Drawing() as draw:
                draw.text_alignment = 'right'
                draw.font_size = 20
                draw.font_weight = 500
                draw.font_family = font
                draw.fill_color = Color('#FFFFFF')
                x = 255 # x offset
                draw.text(x, 60, "Rank: ")
                draw.text(x, 85, "PP: ")
                draw.text(x, 110, "Playcount: ")
                draw.text(x, 135, "Accuracy: ")
                draw(base_img)

            # write user information
            with Drawing() as draw:
                draw.font_size = 26
                draw.font_weight = 500
                draw.font_family = font
                draw.text_alignment = 'center'
                draw.fill_color = Color('#FFFFFF')
                draw.text_decoration = 'underline'
                draw.text(310, 35, user['username'])
                draw(base_img)
            with Drawing() as draw:                
                draw.font_size = 20
                draw.font_weight = 500
                draw.font_family = font
                draw.fill_color = Color('#FFFFFF')
                draw.text_decoration = 'no'
                x = 255 # x offset
                draw.text(x, 60, "#{} (#{})".format(user['pp_rank'], user['pp_country_rank']))
                draw.text(x, 85, "{}".format(user['pp_raw']))
                draw.text(x, 110, "{}".format(user['playcount']))
                draw.text(x, 135, "{}%".format(user['accuracy'][0:5]))
                draw(base_img)

            # draw osu with correct gamemode
            osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
            osu_req = urllib.request.Request(osu_logo_url, headers={'User-Agent': 'Mozilla/5.0'})
            osu = urlopen(osu_req)
            with Image(file=osu) as osu_icon:
                osu_icon.resize(45,45)
                base_img.composite(osu_icon, left=430, top=95)
            osu.close()

            # puts on gamemode, yes, they are in order [standard, taiko, ctb, mania]
            icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
            mode_url = icons_url[gamemode]
            mode_req = urllib.request.Request(mode_url, headers={'User-Agent': 'Mozilla/5.0'})
            mode = urlopen(mode_req)
            with Image(file=mode) as mode_icon:
                mode_icon.resize(43,43)
                base_img.composite(mode_icon, left=385, top=95)
            mode.close()

            # puts on country flag
            flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country'])
            flag_req = urllib.request.Request(flag_url, headers={'User-Agent': 'Mozilla/5.0'})
            flag = urlopen(flag_req)
            with Image(file=flag) as flag_icon:
                flag_icon.resize(30,20) # arbitrary flag size
                base_img.composite(flag_icon, left=440, top=17)
            flag.close()

            # save the image
            base_img.save(filename='data/osu/user.png')
        bg.close()

    # Gives a user profile image with some information
    def draw_user_profile(self, user, userbest, gamemode:int, background:str):
        font = 'Verdana, Geneva, sans-serif'
        key = self.osu_api_key["osu_api_key"]

        # get best plays map titles
        best_beatmaps = []
        for i in range(len(userbest)):
            beatmap = json.loads(get_beatmap(key, beatmap_id=userbest[i]['beatmap_id']).decode("utf-8"))
            best_beatmaps.append(beatmap[0])

        # generate background and crops image to correct size
        # checks if user has stored background
        if background in bgs.keys() and str(background) != 'random':
            bg_url = bgs[background]
        else:
            bg_url = random.choice(list(bgs.values()))  
        bg_req = urllib.request.Request(bg_url, headers={'User-Agent': 'Mozilla/5.0'})
        bg = urlopen(bg_req)
        with Image(file=bg) as base_img:
            # background cropping
            base_img.resize(600,600)
            base_img.crop(0,0,488,488)

            # draw transparent black rectangle
            with Drawing() as draw:
                draw.fill_color = Color('#000000')
                draw.fill_opacity = 0.6
                draw.rectangle(left=10,top=10,right=478,bottom=160)
                draw(base_img)

            # create level graphic
            with Drawing() as draw:
                level_int = int(float(user['level']))
                level_percent = float(user['level']) - level_int
                full_length = 458
                level_length = full_length * level_percent
                draw.fill_color = Color('#FFF')
                draw.fill_opacity = 0.6
                draw.rectangle(left=15,top=145, width=level_length, bottom=155)
                draw(base_img)
            with Drawing() as draw:
                draw.fill_opacity = 1
                draw.text_alignment = 'center'
                draw.font_size = 13
                draw.font_weight = 500
                draw.fill_color = Color('#FFF')
                draw.text(int(base_img.width/2), 155, "Lvl {}".format(str(level_int)))
                draw(base_img)

            # draw transparent white rectangle
            with Drawing() as draw:
                draw.fill_color = Color('#FFFFFF')
                draw.fill_opacity = 0.6
                draw.rectangle(left=10,top=160,right=478,bottom=478)
                draw(base_img)

            # grab user profile image
            profile_url = 'http://s.ppy.sh/a/{}.png'.format(user['user_id'])
            profile_req = urllib.request.Request(profile_url, headers={'User-Agent': 'Mozilla/5.0'})
            profile = urlopen(profile_req)
            with Image(file=profile) as profile_img:
                # user_profile image resizing
                profile_img.resize(130,130)     
                base_img.composite(profile_img, left=10, top=10)
            profile.close()

            # writes lables
            with Drawing() as draw:
                draw.text_alignment = 'right'
                draw.font_size = 20
                draw.font_weight = 500
                draw.fill_color = Color('#FFFFFF')
                x = 255 # x offset
                draw.text(x, 60, "Rank: ")
                draw.text(x, 85, "PP: ")
                draw.text(x, 110, "Playcount: ")
                draw.text(x, 135, "Accuracy: ")
                draw(base_img)

            # write user information
            with Drawing() as draw:
                draw.font_size = 26
                draw.font_weight = 500
                draw.font_family = font
                draw.text_alignment = 'center'
                draw.fill_color = Color('#FFFFFF')
                draw.text_decoration = 'underline'
                draw.text(310, 35, user['username'])
                draw(base_img)
            with Drawing() as draw:                
                draw.font_size = 20
                draw.font_weight = 500
                draw.font_family = font
                draw.fill_color = Color('#FFFFFF')
                draw.text_decoration = 'no'
                x = 255 # x offset
                draw.text(x, 60, "#{} (#{})".format(user['pp_rank'], user['pp_country_rank']))
                draw.text(x, 85, "{}".format(user['pp_raw']))
                draw.text(x, 110, "{}".format(user['playcount']))
                draw.text(x, 135, "{}%".format(user['accuracy'][0:5]))
                draw(base_img)

            # draw osu icon
            osu_logo_url = 'http://puu.sh/pT7JR/577b0cc30c.png'
            osu_req = urllib.request.Request(osu_logo_url, headers={'User-Agent': 'Mozilla/5.0'})
            osu = urlopen(osu_req)
            with Image(file=osu) as osu_icon:
                osu_icon.resize(45,45)      
                base_img.composite(osu_icon, left=430, top=95)
            osu.close()

            # puts on gamemode
            # yes, they are in order [standard, taiko, ctb, mania]
            icons_url=['http://puu.sh/pT2wd/4009301880.png','http://puu.sh/pT7XO/04a636cd31.png', 'http://puu.sh/pT6L5/3528ea348a.png','http://puu.sh/pT6Kl/f5781e085b.png']
            mode_url = icons_url[gamemode]
            mode_req = urllib.request.Request(mode_url, headers={'User-Agent': 'Mozilla/5.0'})
            mode = urlopen(mode_req)
            with Image(file=mode) as mode_icon:
                mode_icon.resize(43,43)      
                base_img.composite(mode_icon, left=385, top=95)
            mode.close()

            # puts on country flag
            flag_url = 'https://new.ppy.sh//images/flags/{}.png'.format(user['country'])
            flag_req = urllib.request.Request(flag_url, headers={'User-Agent': 'Mozilla/5.0'})
            flag = urlopen(flag_req)
            with Image(file=flag) as flag_icon:
                flag_icon.resize(30,20) # arbitrary flag size
                base_img.composite(flag_icon, left=440, top=17)
            flag.close()

            # writes best performances
            with Drawing() as draw:
                draw.font_size = 32
                draw.font_weight = 1000
                draw.font_family = font
                draw.text_alignment = 'center'
                draw.fill_color = Color('#555')
                draw.fill_opacity = 0.6
                draw.text(244, 205, "{}".format('Best Performances'))
                draw(base_img)            

            # create tiles for best plays using top_play_beatmaps and userbest. Includes rank, title, diff, mods, pp, timestamp
            left_align = 20
            top_initial = 230
            spacing = 85

            # draw transparent white rectangles
            for i in range(3):
                with Drawing() as draw:
                    draw.fill_color = Color('#CCC')
                    draw.fill_opacity = 0.6
                    draw.rectangle(left=left_align + 2,top=top_initial + spacing * i - 3, width=445, height = 70)
                    draw(base_img)

            for i in range(len(userbest)): 
                with Drawing() as draw:
                    draw.font_size = 24
                    draw.font_weight = 2000

                    # rank image
                    rank_url = 'https://new.ppy.sh/images/badges/score-ranks/{}.png'.format(userbest[i]['rank'])
                    rank_req = urllib.request.Request(rank_url, headers={'User-Agent': 'Mozilla/5.0'})
                    rank = urlopen(rank_req)
                    with Image(file=rank) as rank_icon:
                        rank_icon.resize(70,70)      
                        base_img.composite(rank_icon, left=left_align + 5, top=top_initial + (i) * spacing)
                    rank.close() 

                    draw.text(left_align + 100, top_initial + 30 + (i) * spacing, "{}".format(self.truncate_text(best_beatmaps[i]['title'])))
                    draw.text(left_align + 100, top_initial + 50 + (i) * spacing, "[{}]".format(self.truncate_text(best_beatmaps[i]['version'])))
                    draw.text(left_align + 335, top_initial + 30 + (i) * spacing, "{:0.2f}pp".format(float(userbest[i]['pp'])))

                    # handle mod images
                    mods = self.mod_calculation(userbest[i]['enabled_mods'])
                    if len(mods) > 0:
                        for j in range(len(mods)):
                            # puts on mod images
                            mod_url = 'https://new.ppy.sh/images/badges/mods/{}.png'.format(mods[j])
                            mod_req = urllib.request.Request(mod_url, headers={'User-Agent': 'Mozilla/5.0'})
                            mod = urlopen(mod_req)
                            with Image(file=mod) as mod_icon:
                                mod_icon.resize(46, 34)
                                base_img.composite(mod_icon, left=left_align + 330 + 45*(j), top=top_initial + 32 + (i) * spacing)
                            mod.close()
                    draw(base_img)

            # save the image
            base_img.save(filename='data/osu/user_profile.png')
        bg.close()

    # Truncates the text because some titles/versions are too long
    def truncate_text(self, text):
        if len(text) > 17:
            text = text[0:15] + '...'
        return text

    # gives a list of the ranked mods given a peppy number lol
    def mod_calculation(self, number):
        number = int(number)
        mod_list =[]

        if number >= 16384:
            number -= 16384
            mod_list.append('perfect')
        if number >= 4096:
            number-= 4096
            mod_list.append('spun-out')
        if number >= 1024:
            number-= 1024
            mod_list.append('flashlight')
        if number >= 576:
            number-= 576
            mod_list.append('nightcore')
        if number >= 256:
            number-= 256
            mod_list.append('half-time')
        if number >= 128:
            number-= 128
            mod_list.append('relax')
        if number >= 64:
            number-= 64
            mod_list.append('double-time')
        if number >= 32:
            number-= 32
            mod_list.append('sudden-death')
        if number >= 16:
            number-= 16
            mod_list.append('hard-rock')
        if number >= 8:
            number-= 8
            mod_list.append('hidden')
        if number >= 2:
            number-= 2
            mod_list.append('easy')
        if number >= 1:
            number-= 1
            mod_list.append('no-fail')
        return mod_list

    async def process_beatmap(self, message):
        key = self.osu_api_key["osu_api_key"]
        beatmap_id = message.content.replace('https://osu.ppy.sh/s/','') 
        beatmap_info = json.loads(get_beatmapset(key, beatmap_id).decode("utf-8"))
        await self.disp_beatmap(message, beatmap_info)
        '''
        except:
            await self.bot.send_message(message.channel, "That beatmap doesn't exist.")
        '''     


    async def disp_beatmap(self, message, beatmap):
        # process time
        ## m, s = divmod(int(beatmap['total_length']), 60)

        await self.bot.send_message(message.channel, "Found {} total maps.\n".format(len(beatmap)))
               
        for i in range(len(beatmap)):
            beatmap_msg = "**{} - {}** [{}] by {}\n".format(beatmap[i]['title'], beatmap[i]['artist'], beatmap[i]['version'], beatmap[i]['creator'])
            beatmap_msg += "**Difficulty:** `{:.2f}` **BPM:** `{}` **Length:** `{}`s \n".format(float(beatmap[i]['difficultyrating']), beatmap[i]['bpm'], beatmap[i]['total_length'])
            beatmap_msg += "**AR:** `{}` **OD:** `{}` **HP:** `{}` **CS:** `{}`\n".format(beatmap[i]['diff_approach'], beatmap[i]['diff_overall'], beatmap[i]['diff_drain'], beatmap[i]['diff_size'])
            await self.bot.send_message(message.channel, beatmap_msg)

    async def check_messages(self, message):
        if message.author.id == self.bot.user.id:
            return

        user = message.author
        test = message.content
        channel = message.channel
        server  = user.server

        if 'https://osu.ppy.sh/s/' in message.content:
            await self.process_beatmap(message)


###-------------------------Python wrapper for osu! api-------------------------

# Returns the full API request URL using the provided base URL and parameters.
def build_request(url_params, url):
    for param in url_params:
        url += str(param)
        if (param != ""):
            url += "&"
    return url[:-1]

# Gets the beatmap
def get_beatmap(key, beatmap_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id)) 

    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_beatmaps?")).read()

# Gets the beatmap set
def get_beatmapset(key, set_id):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("s", set_id)) 

    ## Build the request URLand return the response.
    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_beatmaps?")).read()

# Grabs the scores
def get_scores(key, beatmap_id, user_id, mode):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("b", beatmap_id))   
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_scores?")).read()

def get_user(key, user_id, mode): 
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))

    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_user?")).read()

def get_user_best(key, user_id, mode, limit):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode))
    url_params.append(parameterize_limit(limit)) 

    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_user_best?")).read()

# Returns the user's ten most recent plays.
def get_user_recent(key, user_id, mode, type):
    url_params = []

    url_params.append(parameterize_key(key))
    url_params.append(parameterize_id("u", user_id))
    url_params.append(parameterize_mode(mode)) 

    return urllib.request.urlopen(build_request(url_params, "https://osu.ppy.sh/api/get_user_recent?")).read()

def parameterize_event_days(event_days):
    if (event_days == ""):
        event_days = "event_days=1"
    elif (int(event_days) >= 1 and int(event_days) <= 31):
        event_days = "event_days=" + str(event_days)
    else:
        print("Invalid Event Days")
    return event_days

def parameterize_id(t, id):
    if (t != "b" and t != "s" and t != "u" and t != "mp"):
        print("Invalid Type")
    if (len(str(id)) != 0):
        return t + "=" + str(id)
    else:
        return ""

def parameterize_key(key):
    if (len(key) == 40):
        return "k=" + key
    else:
        print("Invalid Key")   

def parameterize_limit(limit):
    ## Default case: 10 scores
    if (limit == ""):
        limit = "limit=10"
    elif (int(limit) >= 1 and int(limit) <= 50):
        limit = "limit=" + str(limit)
    else:
        print("Invalid Limit")
    return limit
  
def parameterize_mode(mode):
    ## Default case: 0 (osu!)
    if (mode == ""):
        mode = "m=0"
    elif (int(mode) >= 0 and int(mode) <= 3):
        mode = "m=" + str(mode)
    else:
        print("Invalid Mode")
    return mode  

###-------------------------Setup------------------------- 
def check_folders():
    if not os.path.exists("data/osu"):
        print("Creating data/osu folder...")
        os.makedirs("data/osu")

def check_files():
    osu_api_key = {"osu_api_key" : ""}
    api_file = "data/osu/apikey.json"

    if not fileIO(api_file, "check"):
        print("Adding data/osu/apikey.json...")
        fileIO(api_file, "save", osu_api_key)
    else:  # consistency check
        current = fileIO(api_file, "load")
        if current.keys() != osu_api_key.keys():
            for key in system.keys():
                if key not in osu_api_key.keys():
                    current[key] = osu_api_key[key]
                    print("Adding " + str(key) +
                          " field to osu apikey.json")
            fileIO(api_file, "save", current)

    # creates file for user backgrounds
    user_file = "data/osu/user_settings.json"
    if not fileIO(user_file, "check"):
        print("Adding data/osu/user_settings.json...")
        fileIO(user_file, "save", {})

def setup(bot):
    check_folders()
    check_files()

    try: 
        from wand.image import Image, COMPOSITE_OPERATORS
        from wand.drawing import Drawing
        from wand.display import display
        from wand.image import Image
        from wand.color import Color
    except:
        raise ModuleNotFound("Wand is not installed. Do 'pip3 install Wand --upgrade' and make sure you have ImageMagick installed http://docs.wand-py.org/en/0.4.2/guide/install.html")
    n = Osu(bot)
    bot.add_listener(n.check_messages, "on_message")    
    bot.add_cog(n)