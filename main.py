import asyncio
from code import interact
import random
import string
import time
import discord
from itertools import cycle
from discord import colour
from discord.utils import get
from discord.ext import commands, tasks
import json
from flask import ctx
import requests
import blockcypher
from pycoingecko import CoinGeckoAPI
import urllib3
import datetime
from utils.checks import getConfig, updateConfig, getpro, updatepro
from data import fee, your_discord_user_id, WorkspacePath, bot_token, ticket_channel, cancel, apikey, xpubs, menmonics, fees_addy, logs_channel, cat_id

####### API #######

cg = CoinGeckoAPI()

api_key = "075825150dd640fe8de61a130208c44e"

deals = {}

####### FUNCTIONS #######

def usd_to_ltc(amount):
  url = f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD'
  r = requests.get(url)
  d = r.json()
  price = d['USD']
  ltcval = amount/price
  ltcvalf = round(ltcval, 7)
  return ltcvalf

def ltc_to_usd(amount):
  url = f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD'
  r = requests.get(url)
  d = r.json()
  price = d['USD']
  usd = amount*price
  usdf = round(usd, 3)
  return usdf

def create_new_ltc_address(inx) :
  xpub = xpubs
  index = f"{inx}"
  url = "https://api.tatum.io/v3/litecoin/address/" + xpub + "/" + index

  headers = {"x-api-key": apikey}

  response = requests.get(url, headers=headers)

  data = response.json()
  addy = data['address']
  return addy

def get_key(index):
  url = "https://api.tatum.io/v3/litecoin/wallet/priv"

  payload = {
    "index": index,
    "mnemonic": menmonics
  }

  headers = {
    "Content-Type": "application/json",
    "x-api-key": apikey
  }

  response = requests.post(url, json=payload, headers=headers)

  data = response.json()
  key = data['key']
  return key
def get_hash(address):
  endpoint = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full"

  response = requests.get(endpoint)
  data = response.json()


  latest_transaction = data['txs'][0]
  latest_hash = latest_transaction['hash']
  conf = latest_transaction['confirmations']

  return latest_hash, conf

def get_address_balance(address):
    endpoint = f"https://litecoinspace.org/api/address/{address}"
    response = requests.get(endpoint)
    data = response.json()
    balance = data["chain_stats"]["funded_txo_sum"]

    unconfirmed_balance = data['mempool_stats']['funded_txo_sum'] / 10**8
    return balance, unconfirmed_balance


def send_ltc(sendaddy, private_key, recipient_address, amount) :
    url = "https://api.tatum.io/v3/litecoin/transaction"

    payload = {
    "fromAddress": [
        {
        "address": sendaddy,
        "privateKey": private_key
        }
    ],
    "to": [
        {
        "address": recipient_address,
        "value": amount
        }
    ],
    "fee": "0.00005",  
    "changeAddress": fees_addy
    }

    headers = {
    "Content-Type": "application/json",
    "x-api-key": apikey
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    tx = data["txId"]
    return tx

intents = discord.Intents.all()
intents.messages = True

bot_status = cycle([
    "Razon AutoMM", "MADE BY FW_GARY",
    "gg/razon"
])

@tasks.loop(seconds=5)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(bot_status)))

class aclient(commands.Bot):
   
   def __init__(self):
      super().__init__(command_prefix="!", intents=intents, help_command=None)
      self.added = False

   async def on_ready(self):
      print(f'{self.user} has connected to Discord!')
      print('------')
      change_status.start()
      try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        print('------')
      except Exception as e:
        print(e)
        print('------')
      if not self.added:
         self.add_view(middleman_launcher())
         self.added = True
      print("AutoMM BOT Ready")

bot = aclient()

def succeed(message):
    return discord.Embed(description=f"{message}", color=0x32CD32)
def info(message):
    return discord.Embed(description=f"{message}", color=0x32CD32)
def fail(message):
    return discord.Embed(description=f"{message}", color=discord.Color.red()) 
def generate_fid():
  letters = string.ascii_letters
  return "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(36))

@bot.event
async def on_guild_channel_create(channel):
  if channel.category.id == cat_id:
      DEALID = generate_fid()
      deals[DEALID] = {}
      deals[DEALID]['channel'] = channel
      deals[DEALID]['usd'] = None
      deals[DEALID]['ltcid'] = None
      deals[DEALID]['ltcadd'] = None
      deals[DEALID]['stage'] = "ltcid"
      data = getConfig(DEALID)
      data['id'] = DEALID
      updateConfig(DEALID, data)

      await deals[DEALID]['channel'].send(f"```{DEALID}```")

      embed_prompt = discord.Embed(
            title="Razon Auto Middleman System",
            description="> Litecoin Middleman request created successfully!\n\nWelcome to our automated Middleman system!\nYour cryptocurrency will be stored securely for the duration of this deal. Please notify support for assistance.\n.Please note to cancel the deal a staff member will have to review to make sure the cancel is legit. so if you want to cancel ping a staff member",
            color=discord.Color.from_rgb(50, 205, 50)
        )
      embed_prompt.set_thumbnail(url="https://i.postimg.cc/vm8MDHr3/Welcome-Prompt.gif")
      
      embed_security = discord.Embed(
            title="Security Notification",
            description="Our bot and staff team will __NEVER__ direct message you. "
                        "Ensure all conversations related to the deal are done within this ticket. "
                        "Failure to do so may put you at risk of being scammed.",
            color=discord.Color.red()
        )
      
      embed_user = discord.Embed(
            title="Who are you dealing with?",
            description="eg. @user\n"
                "eg. 123456789123456789",
            color=discord.Color.from_rgb(50, 205, 50)
        )
      
      await deals[DEALID]['channel'].send(embed=embed_prompt)
      await deals[DEALID]['channel'].send(embed=embed_security)
      await deals[DEALID]['channel'].send(embed=embed_user)

async def final_middleman(sats, dealid):
  deal = deals[dealid]
  sats_fee = sats * fee
  index = "".join(random.choice("123456789") for _ in range(5))
  inx = int(index)
  data = getConfig(dealid)
  address = create_new_ltc_address(index)
  key = get_key(inx)
  data['addy'] = address
  data['private'] = key
  updateConfig(dealid, data)
  amt_usd = ltc_to_usd(sats_fee)
  amt_ltc = sats_fee
  embed = discord.Embed(
    title=f"📩 Payment Invoice",
    description=f"""<@{data['owner']}> **Send the funds as part of the deal to the Middleman address specified below. Please copy the amount provided.**""",
    color=0x808080
  )
  embed.add_field(
    name="**Address**",
    value=f"`{address}`",
    inline=False
  )
  embed.add_field(
    name=f"**Amount**",
    value=f"`{amt_ltc}` LTC (${amt_usd} USD)",
    inline=False
  )
  embedtwo = discord.Embed()
  embedtwo.set_author(name="Awaiting transaction...", icon_url="https://cdn.discordapp.com/emojis/1098069475573633035.gif?size=96&quality=lossless")
   
   
  await deal['channel'].send(content = f"<@{data['owner']}>",embed=embed,view=PasteButtons(dealid=dealid))
  await deal['channel'].send(embed=embedtwo)

  while 1:
      await asyncio.sleep(5)
      bal, unconfirmed_bal= get_address_balance(data['addy'])
      if unconfirmed_bal >= sats:
          latest_hash, conf = get_hash(data['addy'])
          embed = discord.Embed(title="**Transaction has been detected**",color = 0xFFFF00)
          embed.description=(f"Wait for the transaction to receive the required number of confirmations.")
          embed.add_field(name="**Transaction**", value = f"{latest_hash}[View Transaction](https://blockchair.com/litecoin/transaction/{latest_hash})", inline = False)
          embed.add_field(name="**Required Confirmations**", value = f"`1`", inline = True)
          embed.add_field(name="**Amount Received**", value = f"`{unconfirmed_bal}` LTC (${amt_usd} USD)", inline = True)
          embed.set_thumbnail(url="https://i.postimg.cc/ncFjtJWG/Waiting-Anim.gif")
          embedtwo = discord.Embed()
          embedtwo.set_author(name="Awaiting Confirmation...", icon_url="https://cdn.discordapp.com/emojis/1098069475573633035.gif?size=96&quality=lossless")
          await deal['channel'].send(embed=embed)
          await deal['channel'].send(embed=embedtwo)         
          break
  while 1:
      await asyncio.sleep(5)
      bal, unconfirmed_bal= get_address_balance(data['addy'])
      if bal >= sats:
        latest_hash, conf = get_hash(data['addy'])
      embex = discord.Embed(title="<:check:1291082082445164587> Payment Received",color=0x32CD32)
      embex.description=(f"The payment is now secured, and has reached the required amount of confirmations.")
      embex.add_field(name="**Transaction**", value = f"{latest_hash}[View Transaction](https://blockchair.com/litecoin/transaction/{latest_hash})", inline = False)
      embex.add_field(name="**Confirmations**", value = f"`${conf}`", inline = True)
      embex.add_field(name="**Amount Received**", value = f"`{bal} LTC (${amt_usd} USD)`", inline = True)
      embex.set_thumbnail(url="https://i.postimg.cc/7LGXM7Mh/Money-Receive-Anim.gif")
      embed = discord.Embed(title="**You may now proceed with the deal**", description=f"The receiver (<@{data['reciev']}>) may now provide the goods to the sender (<@{data['owner']}>).\n\nOnce the deal is complete, the sender must click the 'Release' button below to release the funds to the receiver & complete the deal.",color=0x32CD32)
      await deal['channel'].send(content = f"<@{data['reciev']}> <@{data['owner']}>",embed=embed,view=ReleaseButtons(dealid=dealid))
      break

@bot.event
async def on_message(message: discord.Message):
    if message.author.id == bot.user.id:
        return
    for dealid in deals:
        deal = deals[dealid]
        if deal['channel'].id == message.channel.id:
            stage = deal['stage']
            if stage == "ltcid" :
              if message.content in cancel :
                data = getConfig(dealid)
                channel = deals[dealid]['channel']
                await channel.send("Cancelled Deal, `🗑️` Ticket deleting in 5 seconds")
                deals[dealid]['stage'] = "end"
                await channel.edit(name=f"cancelled-{dealid}")
                await asyncio.sleep(5)
                await channel.delete()
                
              if int(message.content) == message.author.id:
                    await message.channel.send(embed=fail("You cannot deal with yourself!"))
              else:  
                    deals[dealid]['ltcid'] = message.content      
                    data = getConfig(dealid)
                    user1_id = message.author.id        
                    user1 = message.guild.get_member(user1_id)

    
                    user_id = int(message.content)
                    user = message.guild.get_member(user_id)
                    channel = deals[dealid]['channel']

                    overwrites = {
                        user : discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        user1 : discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        message.guild.default_role : discord.PermissionOverwrite(read_messages=False)
                    }
                    await channel.edit(overwrites=overwrites)
                    await asyncio.sleep(1)
                    embex1 = discord.Embed(
                    description=f"Successfully added <@{user_id}> to the ticket.",
                    colour=0x32CD32
                    )

                    await channel.send(content=f"<@{user_id}>",embed=embex1)
                    data['owner'] = 0
                    updateConfig(dealid, data)
                    embed = discord.Embed(
                      title="Role Assignment",
                      description="Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
                      color=0x32CD32
                    )
                    embed.add_field(
                      name="**Sending Litecoin**",
                      value=f"`None`",
                      inline=True
                      )
                    embed.add_field(
                      name="**Receiving Litecoin**",
                      value=f"`None`",
                      inline=True
                      )
                    msg1 = await channel.send(embeds=[embex1]) 
                    deals[dealid]['stage'] = "nsns"
                    await msg1.edit(embed=embed, view=SenButtons(dealid=dealid,mnk=msg1.id))

            if stage == "usd":
              data = getConfig(dealid)
              if message.author.id == data['owner']:
                  try:
                      if float(message.content) >= 0.05:
                          deals[dealid]['usd'] = float(message.content)
                          deals[dealid]['stage'] = "ltcadd"
                          data = getConfig(dealid)
                          amt = usd_to_ltc(deal['usd'])
                          data['amount'] = amt
                          updateConfig(dealid, data)
                          embed = discord.Embed(
                            title = "**Amount Confirmation**",
                            description=f"Confirm that the bot will receive the following USD value\n\n**Amount**\n`${float(message.content)}`",
                            color=0xFFFF00
                          )
                          await message.reply(embed=embed, view=conButtons(dealid=dealid))
                      else:
                          await message.reply(embed=fail(f"$1.00 USD Minimum"))
                  except:
                      await message.reply(embed=fail(f"Remove The $ Symbol"))
              else:
                  pass

            if stage == "release":
              data = getConfig(dealid)
              if message.author.id == data['reciev']:
                  try:
                      addy = message.content
                      data = getConfig(dealid)
                      sendaddy = data['addy']
                      amount = data['amount']
                      val = ltc_to_usd(amount)
                      key = data['private']
                      data1 = getpro(data['owner'])
                      data1['deals'] += 1
                      data1['amount'] += val
                      updatepro(data['owner'], data1)
                      data2 = getpro(data['reciev'])
                      data2['deals'] += 1
                      data2['amount'] += val
                      updatepro(data['reciev'], data2)
                      tx = send_ltc(sendaddy,key,addy,amount)
                      embedz = discord.Embed(description=f'The Litecoin has been released successfully to the address provided!\n**Amount**\n`{amount}` LTC (${val} USD)\n**Transaction**\n{tx}\n[View Transaction](https://live.blockcypher.com/ltc/tx/{tx})',colour=0x32CD32,title="💰 Payment Released")
                      await message.reply(embed=embedz)
                      await message.channel.send(f"<@{data['reciev']}> <@{data['owner']}>")
                      greet = discord.Embed(description='Thanks for using our Auto MM! This deal is now marked as complete.\n\nWe hope you are satisfied with our services.',color=0x32CD32,title="Deal Complete!")
                      greet.set_thumbnail(url="https://i.postimg.cc/7LGXM7Mh/Money-Receive-Anim.gif")
                      await message.channel.send(embed=greet)
                      
                      usd_value = ltc_to_usd(data['amount'])
                      embedsk = discord.Embed(title="Litecoin Deal Complete",description=f"**Amount**\n`{data['amount']}` LTC (${usd_value} USD)\n**Sender**\n<@{data['owner']}>\n**Reciever**\n<@{data['reciev']}>\n**Transaction**\n{tx}\n[View Transaction](https://live.blockcypher.com/ltc/tx/{tx})",color=0x32CD32)
                      embedsk.set_thumbnail(url="https://postimg.cc/QKZBJwrG")
                      logs = bot.get_channel(logs_channel)
                      await logs.send(embed=embedsk)
                
                      channel = deals[dealid]['channel']
                      deals[dealid]['stage'] = "doness"
                      await channel.edit(name=f"close")
                      await asyncio.sleep(5)
                   
                      deals[dealid]['stage'] = "doness"
                      await asyncio.sleep(360)
                  except:
                    await message.reply(embed=fail(f"<@{data['reciev']}> Enter Correct Ltc Address"))  

            if stage == "cancel":
              data = getConfig(dealid)
              if message.author.id == data['owner']:
                  channel = message.channel
                  await channel.edit(name="Pending-cancel")
                  await asyncio.sleep(2)
                  await channel.send("This deal is pending cancelation! please wait for the owner to come check it out, if any important messages are deleted the deal will not be canceled and it will go under scam investagation.\n<@1267528622185381930>")
                  '''try:
                      addy = message.content
                      data = getConfig(dealid)
                      amount = data['amount']
                      sendaddy = data['addy']
                      key = data['private']
                      tx = send_ltc(sendaddy,key,addy,amount)
                      await message.reply(f"Transaction ID: [{tx}](https://blockchair.com/litecoin/transaction/{tx})")
                      deals[dealid]['stage'] = "doness"
                  except:
                    await message.reply(embed=fail(f"<@{data['reciev']}> Enter Correct Ltc Address"))'''

@bot.tree.command(name="staff_cancel", description="Allows a staff member to cancel the deal at the request of both parties")
async def staff_cancel(interaction: discord.Interaction, dealid: str, outcome: str, scammer_id: str):
   if interaction.user.id in your_discord_user_id:
      data = getConfig(dealid)
      channel = interaction.channel
      if outcome.lower() == "scam":
         await interaction.response.send_message(f"Deal {dealid} has been marked as an attempted scam please remember to mark the scammer")
         await channel.send(f"Deal {dealid} has been marked as an attempted scam")
         await channel.edit(name=f"ticket-scam-{scammer_id}", sync_permissions=True)
      elif outcome.lower() == "true":
         await interaction.response.send_message(f"Deal {dealid} has been marked as canceled, due to both parties wanted to cancel")
         await channel.edit(name=f"ticket-canceled", sync_permissions=True)

class conButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.channel = deals[dealid]['channel']
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Correct", custom_id=f"sede", style=discord.ButtonStyle.green)
      button.callback = self.sendr1
      self.add_item(button)
      button = discord.ui.Button(label="Incorrect", custom_id=f"rece", style=discord.ButtonStyle.red)
      button.callback = self.recvr1
      self.add_item(button)

  async def sendr1(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    amt = data['amount']
    amt1 = ltc_to_usd(amt)
    if interaction.user.id == data['owner']:
      if data['conf2'] == 1:
        data['conf2'] += 1
        updateConfig(self.dealid, data)
        embed = discord.Embed(description = f"{interaction.user} responded with '**Correct**'",color=0x32CD32)
        await interaction.response.send_message(embed=embed)
        if data['conf1'] == 2:
         
          deals[self.dealid]['stage'] = "ltcadd"
          sender = f"<@{data['owner']}>"  
          receiver = f"<@{data['reciev']}>" 
          value = data['amount'] 
          val = ltc_to_usd(value)  
          coin = "<:ltc:1290350831572488292> Litecoin (LTC)"

          embed = discord.Embed(
          title="📋 Deal Summary",
            description=(
                f"Refer to this deal summary for any reaffirmations. Notify staff for any support required.\n\n"
                f"**Sender:** {sender}\n\n" 
                f"**Receiver:** {receiver}\n\n" 
                f"**Deal Value:** `${val}`\n\n"  
                f"**Coin:** {coin}"  
              ),
            color=0x808080  
          )
          embed.set_thumbnail(url="https://i.postimg.cc/HkWGTS0M/Summary-Anim.gif")
          await interaction.followup.send(embed=embed)
          asyncio.create_task(final_middleman(amt, self.dealid))
          self.stop()
        else:
          pass
    else:
      if data['conf1'] == 1:
        data['conf1'] += 1
        updateConfig(self.dealid, data)
        embed = discord.Embed(description = f"{interaction.user} responded with '**Correct**'",color=0x32CD32)
        await interaction.response.send_message(embed=embed)
        if data['conf2'] == 2:
  
          deals[self.dealid]['stage'] = "ltcadd"
          sender = f"<@{data['owner']}>"  
          receiver = f"<@{data['reciev']}>" 
          value = data['amount'] 
          val = ltc_to_usd(value)  
          coin = "<:ltc:1290350831572488292> Litecoin (LTC)"

          
          embed = discord.Embed(
          title="📋 Deal Summary",
            description=(
                f"Refer to this deal summary for any reaffirmations. Notify staff for any support required.\n\n"
                f"**Sender:** {sender}\n\n" 
                f"**Receiver:** {receiver}\n\n" 
                f"**Deal Value:** `${val}`\n\n"  
                f"**Coin:** {coin}"  
              ),
            color=0x808080  
          )
          embed.set_thumbnail(url="https://i.postimg.cc/HkWGTS0M/Summary-Anim.gif")
          await interaction.followup.send(embed=embed)
          asyncio.create_task(final_middleman(amt, self.dealid))
          self.stop()
        else:
          pass

  async def recvr1(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      embed = discord.Embed(description = f"{interaction.user} responded with '**Incorrect**'",color=0x32CD32)
      data['conf1'] == 0
      data['conf2'] == 0
      updateConfig(self.dealid, data)
      await interaction.response.send_message(embed=embed)
      deals[self.dealid]['stage'] = "usd"
      embed = discord.Embed(title = "**Deal Amount**",description = "State the amount the bot is expected to receive in USD (eg. 100.59)",color=0x32CD32)
      await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
      self.stop()

class confButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Correct", custom_id=f"joindeff", style=discord.ButtonStyle.green)
      button.callback = self.yeske
      self.add_item(button)
      button = discord.ui.Button(label="Incorrect", custom_id=f"joinsdfwef", style=discord.ButtonStyle.danger)
      button.callback = self.noke
      self.add_item(button)

  async def yeske(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['owner']
      rec_id = data['reciev']
      if interaction.user.id == own_id:
        if data['conf1'] == 0:
          data['conf1'] += 1
          updateConfig(self.dealid, data)
          embed = discord.Embed(description = f"{interaction.user} responded with '**Correct**'",color=0x32CD32)
          await interaction.response.send_message(embed=embed)
          if data['conf2'] == 1:
            embed = discord.Embed(title = "**Deal Amount**",description = "State the amount the bot is expected to receive in USD (eg. 100.59)",color=0x32CD32)
            await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
            deals[self.dealid]['stage'] = "usd"
          else: 
            pass
        else:
          embed = discord.Embed(description = f"You have already responded")
          await interaction.response.send_message(embed=embed)         
      else:
        if data['conf2'] == 0:
          data['conf2'] += 1
          updateConfig(self.dealid, data)
          embed = discord.Embed(description = f"{interaction.user} responded with '**Correct**'",color=0x32CD32)
          await interaction.response.send_message(embed=embed)
          if data['conf1'] == 1:
            embed = discord.Embed(title = "**Deal Amount**",description = "State the amount the bot is expected to receive in USD (eg. 100.59)",color=0x32CD32)
            await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
            deals[self.dealid]['stage'] = "usd"
          else:
            pass

        else:
          embed = discord.Embed(description = f"You have already responded")
          await interaction.response.send_message(embed=embed)

  async def noke(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    own_id = data['owner']
    rec_id = data['reciev']
    embed = discord.Embed(description = f"{interaction.user} responded with '**Incorrect**'",color=0x32CD32)
    await interaction.response.send_message(embed=embed)
    embed1 = discord.Embed(
      title="Role Assignment",
      description="**Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.**",
     color=0x32CD32
    )
    embed1.add_field(
      name="**Sending Litecoin**",
      value=f"None",
      inline=True
      )
    embed1.add_field(
      name="**Receiving Litecoin**",
      value=f"None",
      inline=True
      )
    msg1 = await interaction.followup.send(content = f"<@{own_id}> <@{rec_id}>", embed=embed1)
    await msg1.edit(embed=embed1, view=SenButtons(dealid=self.dealid,mnk=msg1.id))
                                                                                                      
class SenButtons(discord.ui.View) :
  def __init__(self, dealid, mnk) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.msg_id = mnk
      self.channel = deals[dealid]['channel']
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Sending", custom_id=f"sed", style=discord.ButtonStyle.gray)
      button.callback = self.sendr
      self.add_item(button)
      button = discord.ui.Button(label="Receiving", custom_id=f"rec", style=discord.ButtonStyle.gray)
      button.callback = self.recvr
      self.add_item(button)
      button = discord.ui.Button(label="Reset", custom_id=f"fien", style=discord.ButtonStyle.red)
      button.callback = self.reset
      self.add_item(button)

  async def sendr(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['owner'] = interaction.user.id
    updateConfig(self.dealid, data)
    if data['owner'] != data['reciev']:
      data['owner'] = interaction.user.id
      updateConfig(self.dealid, data)
      if data['reciev'] == 1:
        embed = discord.Embed(
          title="Role Assignment",
          description="**Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.**",
          color=0x32CD32
        )
        embed.add_field(
          name="**Sending Litecoin**",
          value=f"<@{data['owner']}>",
          inline=True
        )
        embed.add_field(
          name="**Receiving Litecoin**",
          value=f"None",
          inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.edit(embed=embed)

      else:
        embed = discord.Embed(
          title="Role Assignment",
          description="Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
          color=0x32CD32
        )
        embed.add_field(
          name="**Sending Litecoin**",
          value=f"<@{data['owner']}>",
          inline=True
        )
        embed.add_field(
          name="**Receiving Litecoin**",
          value=f"<@{data['reciev']}>",
          inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.delete()
        embed1 = discord.Embed(title = "Confirm Roles",color=0x32CD32)
        embed1.add_field(
          name="**Sender**",
          value=f"<@{data['owner']}>",
          inline=True
          )
        embed1.add_field(
          name="**Receiver***",
          value=f"<@{data['reciev']}>",
          inline=True
          )
        
        embed1.add_field(
          name="Warning",
          value="Selecting the wrong role will result in getting scammed",
          inline=False
          )
        
        await interaction.response.send_message(embed=embed1,view=confButtons(dealid=self.dealid))
   

 
  async def recvr(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['reciev'] = interaction.user.id
    updateConfig(self.dealid, data)
    if data['reciev'] != data['owner']:
      data['reciev'] = interaction.user.id
      updateConfig(self.dealid, data)
      if data['owner'] == 0:
        embed = discord.Embed(
          title="Role Assignment",
          description="Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
          color=0x32CD32
        )
        embed.add_field(
        name="**Sending Litecoin**",
        value=f"`None`",
        inline=True
        )
        embed.add_field(
        name="**Receiving Litecoin**",
        value=f"<@{data['reciev']}>",
        inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.edit(embed=embed)

      else:
        embed = discord.Embed(
          title="Role Assignment",
          description="Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
          color=0x32CD32
        )
        embed.add_field(
        name="**Sending Litecoin**",
        value=f"<@{data['owner']}>",
        inline=True
        )
        embed.add_field(
        name="**Receiving Litecoin**",
        value=f"<@{data['reciev']}>",
        inline=True
        )
        embed1 = discord.Embed(title = "Confirm Roles",color=0x32CD32)
        embed1.add_field(
          name="**Sender**",
          value=f"<@{data['owner']}>",
          inline=True
          )
        embed1.add_field(
          name="**Receiver**",
          value=f"<@{data['reciev']}>",
          inline=True
          )
        
        embed1.add_field(
          name="Warning",
          value="Selecting the wrong role will result in getting scammed",
          inline=False
          )
        await interaction.response.send_message(embed=embed1,view=confButtons(dealid=self.dealid))
    else:
        await interaction.response.send_message(f"**You can't do that!**",ephemeral=True)
                                     
                                     
  async def done(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    if data['reciev'] == 1:
      await interaction.response.send_message(f"**Must specify reciever**",ephemeral=True)
    if data['owner'] == 0:
      await interaction.response.send_message(f"**must specify sender**",ephemeral=True)
    if data['owner'] == data['reciev']:
      await interaction.response.send_message(f"**You cant be both sender and reciever**",ephemeral=True)
    if interaction.user.id == data['owner']:
      message = await self.channel.fetch_message(self.msg_id)
      await message.edit(view=None)
      embed = discord.Embed(title = "**Deal Amount**",description = "State the amount the bot is expected to receive in USD (eg. 100.59)",color=0x32CD32)
      await interaction.response.send_message(content = f"<@{data['owner']}>",embed=embed)
      deals[self.dealid]['stage'] = "usd"
    else:
      await interaction.response.send_message(embed=fail("Only Sender can Confirm"),ephemeral=True)

  async def reset(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['reciev'] = 1
    data['owner'] = 0
    updateConfig(self.dealid,data)
    embed = discord.Embed(
      title="Role Assignment",
      description="Select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.",
      color=0x32CD32
    )
    embed.add_field(
      name="**Sending Litecoin**",
      value=f"`None`",
      inline=True
      )
    embed.add_field(
      name="**Receiving Litecoin**",
      value=f"`None`",
      inline=True
      )
    message = await self.channel.fetch_message(self.msg_id)
    await message.edit(embed=embed)
                                                             
class cancelButtons(discord.ui.View) :
    def __init__(self, dealid) :
        super().__init__(timeout=None)
        self.dealid = dealid
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Yes", custom_id=f"joind", style=discord.ButtonStyle.green)
        button.callback = self.yesk
        self.add_item(button)
        button = discord.ui.Button(label="No", custom_id=f"joinsd", style=discord.ButtonStyle.danger)
        button.callback = self.nok
        self.add_item(button)

    async def yesk(self, interaction: discord.Interaction):
        data = getConfig(self.dealid)
        own_id = data['reciev']
        if interaction.user.id == own_id:
            deals[self.dealid]['stage'] = "cancel"
            await interaction.response.send_message(embed=succeed("## Provide your Litecoin address\n\nThe deal is now complete! Paste your Litecoin address below to initiate the release from the Middleman wallet."))
            await interaction.followup.send(content="Please verify that the address you provided is correct. Once the funds are released, they cannot be retrieved.")
            await interaction.followup.send(f"<@{data['reciev']}>")
            self.stop()
        else:
           await interaction.response.send_message(embed=fail("You Are not the reciever of this deal"))

    async def nok(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['reciev']
      await interaction.response.send_message(embed=succeed("Contact Owner To get back payement"))
      self.stop()

class PasteButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Copy Details", custom_id=f"joinsff", style=discord.ButtonStyle.gray)
      button.callback = self.release77
      self.add_item(button)


  async def release77(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      addy = data['addy']
      amount = data['amount'] * fee
      await interaction.response.send_message(content=f"{addy}")
      await interaction.followup.send(content=f"{amount}")
      self.stop()

class ReleaseButtons(discord.ui.View) :
    def __init__(self, dealid) :
        super().__init__(timeout=None)
        self.dealid = dealid
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Release", custom_id=f"join", style=discord.ButtonStyle.green)
        button.callback = self.release
        self.add_item(button)
        button = discord.ui.Button(label="cancel", custom_id=f"joins", style=discord.ButtonStyle.danger)
        button.callback = self.cancel
        self.add_item(button)

    async def release(self, interaction: discord.Interaction):
        data = getConfig(self.dealid)
        own_id = data['owner']
        if interaction.user.id == own_id:
            deals[self.dealid]['stage'] = "release"
            await interaction.response.send_message(embed=succeed("## Provide your Litecoin address\n\nThe deal is now complete! Paste your Litecoin address below to initiate the release from the Middleman wallet."))
            await interaction.followup.send(content="Please make sure that the address you provided is 100% yours. Once the funds are released, they cannot be retrieved. If you pasted the wrong address we are not responsible for the loss of funds.")
            await interaction.followup.send(f"<@{data['reciev']}>")
            self.stop()
        else:
           await interaction.response.send_message(embed=fail("You Are not the sender of this deal"))

    async def cancel(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['owner']
      await interaction.response.send_message(embed=succeed("Are you sure you want to cancel this deal?"),view=cancelButtons(self.dealid))
      self.stop()

class middleman_launcher(discord.ui.View):
   def __init__(self) -> None:
      super().__init__(timeout=None)
   
   @discord.ui.button(label='AutoMM ticket',
                      style=discord.ButtonStyle.blurple,
                      custom_id='AutoMM_ticket')
   async def AutoMM_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
      guild = interaction.guild
      category = discord.utils.get(guild.categories, id=cat_id)
      overwrites = {
         interaction.guild.default_role:
         discord.PermissionOverwrite(view_channel=False),
         interaction.user:
         discord.PermissionOverwrite(view_channel=True,
                                     send_messages=True,
                                     attach_files=True,
                                     embed_links=True),
         interaction.guild.me:
         discord.PermissionOverwrite(view_channel=True,
                                     send_messages=True,
                                     attach_files=True,
                                     embed_links=True),
                                     }
      channel = await guild.create_text_channel(name=f"automm-ticket-{interaction.user.display_name}",
                                                overwrites=overwrites,
                                                category=category,
                                                reason=f"Automm for {interaction.user}")
      await interaction.response.send_message(content = f"Your ticket has been created in {channel.mention}!", ephemeral=True )

class scamButtons(discord.ui.View):
   def __init__(self) -> None:
      super().__init__(timeout=None)

   @discord.ui.button(label="Report scam",
                      style=discord.ButtonStyle.red,
                      custom_id='report-scam')
   async def report_scam(self, interaction: discord.Interaction, button: discord.ui.Button):
      guild = interaction.guild
      channel = interaction.channel
      await channel.edit(name="ticket-needReview")
      await interaction.response.send_message(embed=succeed("Ticket reported! A staff will be with you shortly to review it. Please try to not ping staff."))

@bot.tree.command(name="get_private_key",description="Get The Private Key Of A Wallet")
async def GETKEY(interaction: discord.Interaction, deal_id: str):
    if interaction.user.id in your_discord_user_id:
        data = getConfig(deal_id)
        key = data['private']
        await interaction.response.send_message(embed=info(key))
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))

@bot.tree.command(name="get_wallet_balance",description="Get The Balance Of A Wallet")
async def GETBAL(interaction: discord.Interaction, address: str):
    balltc, unballtc = get_address_balance(address)
    balusd = ltc_to_usd(balltc)
    unbalusd = ltc_to_usd(unballtc)
    embed = discord.Embed(title=f"Address {address}",description=f"**Balance**\n\nUSD: {balusd}\nLTC: {balltc}\n\n**Unconfirmed Balance**\n\nUSD: {unbalusd}\nLTC: {unballtc}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="send" ,description="Send Litecoin to a wallet")
async def SEND(interaction: discord.Interaction, deal_id: str, addy: str, amt: float):
  if interaction.user.id in your_discord_user_id:
    data = getConfig(deal_id)
    await interaction.response.send_message(content = "Sending Litecoin")
    onr = data['reciev']
    amount = usd_to_ltc(amt)
    key = data['private']
    sendaddy = data['addy']
    tx = send_ltc(sendaddy,key,addy,amount)
    await interaction.followup.send(content =  f"[{tx}](https://live.blockcypher.com/ltc/tx/{tx})",embed=succeed(f"Transaction ID: [{tx}](https://live.blockcypher.com/ltc/tx/{tx})"))
  else:
    await interaction.response.send_message(embed=fail("Only Admins Can Do This"))

@bot.tree.command(name="mark", description="Marks a user as a scammer with a reason")
async def MARK(interaction: discord.Interaction, *, user: discord.Member, reason: str):
   if interaction.user.id in your_discord_user_id:
      data = getpro(user.id)
      guild = interaction.guild
      if data == None:
         await interaction.response.send_message(embed=fail("User is not found please try again with the markID command!"))
      else:
         if data["scammer"] == "True":
            await interaction.response.send_message(embed=fail("User is already marked as a scammer!"))
         elif data["scammer"] == "False":
            await interaction.response.send_message(embed=succeed("User has been marked as a scammer!"))
            channel = guild.get_channel(1297938416964735017)
            await channel.send(f"{user.name} : {user.id} has been marked as a scammer! Reason: {reason}")
            data["scammer"] = "True"
            data["scammerreason"] = reason
            updatepro(user.id, data)

@bot.tree.command(name="unmark", description="Unmarks a user")
async def UNMARK(interaction: discord.Interaction, *, user: discord.Member):
   if interaction.user.id in your_discord_user_id:
      data = getpro(user.id)
      if data == None:
         await interaction.response.send_message(embed=fail("User is not found please try again with the markID command!"))
      else:
         if data["scammer"] == "True":
            await interaction.response.send_message(embed=succeed("User has been unmarked as a scammer!"))
            data["scammer"] = "False"
            data["scammerreason"] = "None"
            updatepro(user.id, data)
         elif data["scammer"] == "False":
            await interaction.response.send_message(embed=fail("User is not marked!"))

@bot.tree.command(name="markid", description="Marks a user ID as a scammer with a reason")
async def MARKID(interaction: discord.Interaction, *, user: str, reason: str):
   if interaction.user.id in your_discord_user_id:
      guild = interaction.guild
      data = getpro(user)
      if data == None:
         await interaction.response.send_message(embed=fail("User is not found!"))
      else:
         if data["scammer"] == "True":
            await interaction.response.send_message(embed=fail("User is already marked as a scammer!"))
         elif data["scammer"] == "False":
            await interaction.response.send_message(embed=succeed("User has been marked as a scammer!"))
            channel = guild.get_channel(1297938416964735017)
            await channel.send(f"<@{user}> : {user} has been marked as a scammer! Reason: {reason}")
            data["scammer"] = "True"
            data["scammerreason"] = reason
            updatepro(user, data)

@bot.tree.command(name="unmarkid", description="Unmarks a user ID")
async def UNMARKID(interaction: discord.Interaction, *, user: str):
   if interaction.user.id in your_discord_user_id:
      data = getpro(user)
      if data == None:
         await interaction.response.send_message(embed=fail("User is not found!"))
      else:
         if data["scammer"] == "True":
            await interaction.response.send_message(embed=succeed("User has been unmarked as a scammer!"))
            data["scammer"] = "False"
            data["scammerreason"] = "None"
            updatepro(user, data)
         elif data["scammer"] == "False":
            await interaction.response.send_message(embed=fail("User is not marked!"))

@bot.tree.command(name="profile",description="Get The Profile of a User")
async def GETPRO(interaction: discord.Interaction, *, user: discord.User = None):
  if user == None:
    data = getpro(interaction.user.id)
    if data['scammer'] == "False":
      deal = data['deals']
      amount = data['amount']
      badges = data['badges']
      embed = discord.Embed(title=f"{interaction.user.name}",description=f"**Role**: {badges}\n**User ID** -> {interaction.user.id}\n**User** -> {interaction.user.mention}\n**User Stats**\n\n>>>  Total Deals : {deal}\n  Total Ammount : {amount}")
      await interaction.response.send_message(embed=embed)
    else:
       scammer_reason = data['scammerreason']
       embed=discord.Embed(title=f"`{interaction.user.name}` is a SCAMMER!", color=0xff0000)
       embed.add_field(name="", value="**MARKED BY STAFF**", inline=False)
       embed.add_field(name="This User was Marked For:", value=f"{scammer_reason}")
       embed.set_footer(text="Created by Gary | Razon | discord.gg/razon")
       await interaction.response.send_message(embed=embed)
  else:
    data = getpro(user.id)
    if data['scammer'] == "False":
      deal = data['deals']
      amount = data['amount']
      badges = data['badges']
      embed = discord.Embed(title=f"{user.name}",description=f"**Role**: {badges}\n**User ID** -> {user.id}\n**User** -> {user.mention}\n**User Stats**\n\n>>>  Total Deals : {deal}\n  Total Ammount : {amount}")
      await interaction.response.send_message(embed=embed)
    else:
      scammer_reason = data['scammerreason']
      embed=discord.Embed(title=f"`{user.name}` is a SCAMMER!", color=0xff0000)
      embed.add_field(name="", value="**MARKED BY STAFF**", inline=False)
      embed.add_field(name="This User was Marked For:", value=f"{scammer_reason}")
      embed.set_footer(text="Created by Gary | Razon | discord.gg/razon")
      await interaction.response.send_message(embed=embed)

@bot.tree.command(name="launch_mm", description="Launches the Auto MM Ticket service")
async def launchAutoMM(interaction: discord.Interaction):
   if interaction.user.id in your_discord_user_id:
      await interaction.response.send_message(content = "Launching Auto MM Ticket Service", ephemeral=True)
      guild = interaction.guild
      automm_embed = discord.Embed(title="AutoMM Ticket", color=discord.Color.blurple())
      automm_embed.add_field(name="What is A AutoMM", value="An AutoMM is an automatic middleman service. Which has a 4% fee. The bot is made to ensure the security of both parties using the bot. Always use MM when dealing with anyone.", inline=False)
      automm_embed.add_field(name="Is This Safe ?", value="Yes it is safe, only the person who sent the money can release the money to the receiver. The receiver can't take the money without the sender's permission. You can contact support if you have any problems.", inline=False)
      automm_embed.add_field(name="How Do I Use It ?", value="To use the AutoMM just create a ticket and follow the instructions it gives.", inline=False)
      channel = discord.utils.get(guild.channels, id=ticket_channel)
      await channel.send(embed=automm_embed, view=middleman_launcher())



bot.run(bot_token)