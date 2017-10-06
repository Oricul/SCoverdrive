import discord, json, aiohttp, asyncio, linecache, sys
from discord.ext import commands
from .printoverride import print as print

def ReportException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename,lineno,f.f_globals)
    print('Error on line: {}.\nCode: {}\nException: {}'.format(lineno,line.strip(),exc_obj))
    return

jsonfile = "OD"
try:
    with open('./{}.json'.format(jsonfile), 'r+', encoding="UTF-8") as secretfile:
        sec = json.load(secretfile)
        introChannelID = sec['OVERDRIVE']['introChannelID']
        orgSID = sec['OVERDRIVE']['orgSID']
        approveEmoji = sec['OVERDRIVE']['approveEmoji']
        approveRole = sec['OVERDRIVE']['approveRole']
        affiliateEmoji = sec['OVERDRIVE']['affiliateEmoji']
        affiliateRole = sec['OVERDRIVE']['affiliateRole']
        pendingEmoji = sec['OVERDRIVE']['pendingEmoji']
except FileNotFoundError:
    exit("{}.json is not in the current bot directory.".format(jsonfile))

class core:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self,message):
        if (message.author.id != self.bot.user.id):
            try:
                findDot = message.content.find(".")
            except:
                findDot = 0
                pass
            try:
                findSpace = message.content.find(" ")
            except:
                findSpace = 0
                pass
            if (findDot - 2 != 0) and not ("od" in message.content[:findDot]) and (self.bot.commands.get(message.content[findDot:findSpace]) is None):
                if "https://robertsspaceindustries.com/citizens/" in message.content and (message.channel.id == introChannelID):
                    urlCheck = message.content.find("https://robertsspaceindustries.com/citizens/")
                    correctURL = message.content[urlCheck:]
                    if " " in correctURL:
                        correctURL = correctURL[:correctURL.find(" ")]
                    if "organizations" in correctURL:
                        correctURL = correctURL[:-14]
                    foundHandle = correctURL[correctURL.rfind("/")+1:]
                    getURL = "http://sc-api.com/?data_source=RSI&api_source=live&system=accounts&action=full_profile&target_id={}".format(
                        foundHandle)
                    headers = {'content-type': 'application/json'}
                    while True:
                        try:
                            session = aiohttp.ClientSession()
                            async with session.post(getURL, headers=headers) as resp:
                                allFound = (await resp.json())['data']
                                await session.close()
                                break
                        except:
                            try:
                                await session.close()
                            except:
                                pass
                            await asyncio.sleep(2.5)
                            pass
                    try:
                        found = allFound['organizations']
                    except:
                        await self.bot.add_reaction(message, "{}".format(pendingEmoji))
                        embed = discord.Embed(colour=discord.Colour(0xFFFF00),
                                              description="You have no visible orgs. Fix this and try again.".format(
                                                  message.author))
                        embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                        embed.set_thumbnail(url=allFound['avatar'])
                        await self.bot.send_message(message.channel, embed=embed)
                        return
                    orgFound = 0
                    for i in found:
                        if (i['sid'] != ""):
                            if (i['sid'].upper() == orgSID.upper()):
                                orgFound = 1
                                break
                    if orgFound:
                        if (found[0]['sid'].upper() == orgSID.upper()):
                            await self.bot.add_reaction(message,"{}".format(approveEmoji))
                            embed = discord.Embed(colour=discord.Colour(0x00FF00),
                                                  description="You've been detected as a member. Welcome aboard.")
                            embed.set_author(name=allFound['handle'].title(),icon_url=allFound['avatar'])
                            embed.set_thumbnail(url=allFound['avatar'])
                            for i in message.server.roles:
                                if (approveRole.upper() == i.name.upper()):
                                    await self.bot.add_roles(message.author,i)
                                    break
                            await self.bot.change_nickname(message.author,foundHandle)
                            await self.bot.send_message(message.channel,embed=embed)
                        else:
                            await self.bot.add_reaction(message,"{}".format(affiliateEmoji))
                            embed = discord.Embed(colour=discord.Colour(0x00FF00),
                                                  description="You've been detected as an affiliate. Welcome.")
                            embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                            embed.set_thumbnail(url=allFound['avatar'])
                            for i in message.server.roles:
                                if (affiliateRole.upper() == i.name.upper()):
                                    await self.bot.add_roles(message.author,i)
                                    break
                            await self.bot.change_nickname(message.author, foundHandle)
                            await self.bot.send_message(message.channel,embed=embed)
                    else:
                        await self.bot.add_reaction(message,"{}".format(pendingEmoji))
                        embed = discord.Embed(colour=discord.Colour(0xFFFF00),
                                              description="Your org is hidden, redacted or you are not a member. Fix this and try again.".format(
                                                  message.author))
                        embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                        embed.set_thumbnail(url=allFound['avatar'])
                        await self.bot.send_message(message.channel,embed=embed)

    @commands.command(pass_context=True,hidden=True)
    async def emojis(self,ctx):
        try:
            await self.bot.delete_message(ctx.message)
        except:
            pass
        if (ctx.message.author.bot == False):
            if (ctx.message.author.server_permissions.administrator == True):
                for i in self.bot.get_all_emojis():
                    await self.bot.send_message(ctx.message.author,"{0} `{0}`".format(i))
            else:
                await self.bot.send_message(ctx.message.author,"You are not authorized to use this command.")
        return

    @commands.command(pass_context=True,hidden=True)
    async def roles(self,ctx):
        try:
            await self.bot.delete_message(ctx.message)
        except:
            pass
        if (ctx.message.author.bot == False):
            if (ctx.message.author.server_permissions.administrator == True):
                for i in ctx.message.server.roles:
                    await self.bot.send_message(ctx.message.author,"{} {}".format(i,i.id))
            else:
                await self.bot.send_message(ctx.message.author,"You are not authorized to use this command.")
        return

    @commands.command(pass_context=True,hidden=True)
    async def recheck(self,ctx,userName,handle):
        userName = ctx.message.server.get_member(userName[2:-1])
        try:
            await self.bot.delete_message(ctx.message)
        except:
            pass
        if (ctx.message.author.bot == False):
            if (ctx.message.author.server_permissions.administrator == True):
                session = aiohttp.ClientSession()
                getURL = "http://sc-api.com/?data_source=RSI&api_source=live&system=accounts&action=full_profile&target_id={}".format(
                    handle)
                headers = {'content-type': 'application/json'}
                async with session.post(getURL, headers=headers) as resp:
                    allFound = (await resp.json())['data']
                    found = allFound['organizations']
                    session.close()
                orgFound = 0
                orgList = ""
                for i in found:
                    if (i['sid'] != ""):
                        orgList = "{}\n{}".format(orgList,(i['sid']))
                        if (i['sid'].upper() == orgSID.upper()):
                            orgFound = 1
                            break
                if orgFound:
                    if (found[0]['sid'].upper() == orgSID.upper()):
                        embed = discord.Embed(colour=discord.Colour(0x00FF00),
                                              description="{} has been detected as a member.".format(handle))
                        embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                        embed.set_thumbnail(url=allFound['avatar'])
                        for i in ctx.message.server.role_hierarchy:
                            if (approveRole.upper() == i.name.upper()):
                                await self.bot.add_roles(userName, i)
                                break
                        await self.bot.change_nickname(userName, handle)
                        await self.bot.send_message(ctx.message.channel, embed=embed)
                    else:
                        embed = discord.Embed(colour=discord.Colour(0x00FF00),
                                              description="{} has been detected as an affiliate.".format(handle))
                        embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                        embed.set_thumbnail(url=allFound['avatar'])
                        for i in ctx.message.server.roles:
                            if (affiliateRole.upper() == i.name.upper()):
                                await self.bot.add_roles(userName, i)
                                break
                        await self.bot.change_nickname(userName, handle)
                        await self.bot.send_message(ctx.message.channel, embed=embed)
                else:
                    embed = discord.Embed(colour=discord.Colour(0xFFFF00),
                                          description="Still not found. Please verify manually.\nDetected:{}".format(
                                              orgList))
                    embed.set_author(name=allFound['handle'].title(), icon_url=allFound['avatar'])
                    embed.set_thumbnail(url=allFound['avatar'])
                    await self.bot.send_message(ctx.message.channel, embed=embed)
        return


def setup(bot):
    bot.add_cog(core(bot))