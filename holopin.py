from typing import Type
import urllib.parse
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import RoomCreatePreset
from maubot import Plugin, MessageEvent
from maubot.handlers import command


class Config(BaseProxyConfig):

  def do_update(self, helper: ConfigUpdateHelper) -> None:
    helper.copy("api_key")
    helper.copy("issuers")
    helper.copy("badges")

class HolopinPlugin(Plugin):

  async def start(self) -> None:
    self.config.load_and_update()

  @command.new("holopin", require_subcommand=True)
  async def holopin(self, event: MessageEvent) -> None:
    pass    

  @holopin.subcommand(help="Award a badge to a list of users, e.g. !holopin award hackathon @user1:matrix.org @user2:matrix.org")
  @command.argument("argument", pass_raw=True, required=True)
  async def award(self, event: MessageEvent, argument: str) -> None:
    await event.mark_read()

    if argument and len(argument.split()) >= 2:
      # Split input 
      argument_parts = argument.split()
      badge_alias = argument_parts[0]
      users = argument_parts[1:]
    else:
      await event.reply(f"Please provide a badge alias and at least one Matrix user that shall be awarded.")
      return None

    if event.sender in self.config["issuers"]:
      # Read configured API Key
      api_key = self.config["api_key"]
      # Get badge information from list of configured badge aliases
      badges = self.config["badges"]
      if badge_alias in badges.keys():
        badge_id = badges[badge_alias]["id"]
      else:
        await event.reply(f"{badge_alias} was not found in list of available badges. Choose one from {','.join(badges.keys())}")
        return None
      # Construct API URL
      url_params = urllib.parse.urlencode({"id": badge_id, "apiKey": api_key})
      url = "https://www.holopin.io/api/sticker/share?{}".format(url_params)
      for user in users:
        response = await self.http.post(url, json={"email": ""})
        if response.status == 200:
          success_response = await response.json()
          claim_id = success_response['data']['id']
          claim_url = "https://holopin.io/claim/" + claim_id
          # Send message to a private chat
          # TODO: This will create a new room with every call. Reusing an old private chat is not trivial with Matrix.
          room_id = await self.client.create_room(preset=RoomCreatePreset.TRUSTED_PRIVATE, invitees=[user], is_direct=True)
          await self.client.send_notice(room_id, text=f"Congratulations! Claim your brand new badge at {claim_url}")
          # Confirm success to the issuer
          await event.reply(f"Successfully sent badge to {user}.")
        else:
          await event.reply(f"Issuing the badge {badge_id} failed wit error {response.status}.")
      return None
    else:
      await event.reply(f"You're not allowed to award badges.")
      return None

  @classmethod
  def get_config_class(cls) -> Type[BaseProxyConfig]:
    return Config
