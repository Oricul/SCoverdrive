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
        orgSID = sec['OVERDRIVE']['orgSID']
        approveRole = sec['OVERDRIVE']['approveRole']
        affiliateRole = sec['OVERDRIVE']['affiliateRole']
        serverID = sec['OVERDRIVE']['serverID']
        checkDelay = sec['OVERDRIVE']['checkDelay']
except FileNotFoundError:
    exit("{}.json is not in the current bot directory.".format(jsonfile))

class timed:
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.orgCheck())

    async def orgCheck(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            print(">> Performing automated check of members.")
            try:
                servObj = self.bot.get_server(serverID)
                servMem = []
                for initMember in servObj.members:
                    servMem.append(initMember)
                session = aiohttp.ClientSession()
                getURL = "http://sc-api.com/?api_source=live&system=organizations&action=organization_members&target_id=OVERDRIVE&start_page=1&end_page=999"
                headers = {'content-type': 'application/json'}
                while True:
                    try:
                        async with session.post(getURL, headers=headers) as resp:
                            allFound = (await resp.json())['data']
                            break
                    except Exception as e:
                        print("ERROR: {}".format(e))
                        await session.close()
                        await asyncio.sleep(120)
                        session = aiohttp.ClientSession()
                        print("RETRYING...")
                        pass
                for dMember in servMem:
                    for dRole in dMember.roles:
                        if (dRole.name.upper() == approveRole.upper()):
                            if " " in dMember.display_name:
                                print("MEMBER ({0}) has a SPACE in their HANDLE, which CAN'T happen.".format(dMember))
                                await self.bot.remove_roles(dMember,dRole)
                                continue
                            foundMember = 0
                            for orgMember in allFound:
                                if orgMember['handle'] is not None:
                                    if (dMember.display_name.upper() == orgMember['handle'].upper()):
                                        foundMember = 1
                                        if (orgMember['type'].upper() != "MAIN"):
                                            for servRole in servObj.roles:
                                                if (servRole.name.upper() == affiliateRole.upper()):
                                                    print("MEMBER ({0}) detected as AFFILIATE.".format(dMember))
                                                    await self.bot.remove_roles(dMember,dRole)
                                                    await asyncio.sleep(2.5)
                                                    await self.bot.add_roles(dMember,servRole)
                                                    break
                            if not foundMember:
                                print("MEMBER ({0}) NOT DETECTED.".format(dMember))
                                await self.bot.remove_roles(dMember,dRole)
                        elif (dRole.name.upper() == affiliateRole.upper()):
                            if " " in dMember.display_name:
                                print("AFFILIATE ({0}) has a SPACE in their HANDLE, which CAN'T happen.".format(dMember))
                                await self.bot.remove_roles(dMember,dRole)
                                continue
                            foundMember = 0
                            for orgMember in allFound:
                                if orgMember['handle'] is not None:
                                    if (dMember.display_name.upper() == orgMember['handle'].upper()):
                                        foundMember = 1
                                        if (orgMember['type'].upper() != "AFFILIATE"):
                                            for servRole in servObj.roles:
                                                if (servRole.name.upper() == approveRole.upper()):
                                                    print("AFFILIATE ({0}) detected as MEMBER.".format(dMember))
                                                    await self.bot.remove_roles(dMember,dRole)
                                                    await asyncio.sleep(2.5)
                                                    await self.bot.add_roles(dMember,servRole)
                                                    break
                            if not foundMember:
                                print("AFFILIATE ({0}) NOT DETECTED.".format(dMember))
                                await self.bot.remove_roles(dMember,dRole)
                        await asyncio.sleep(2.5)
            except Exception as e:
                error = ReportException()
                print("{0}\n{1}".format(error, e))
                pass
            print(">> Automated check complete. Sleeping.")
            await asyncio.sleep(int(checkDelay))

def setup(bot):
    bot.add_cog(timed(bot))