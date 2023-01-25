from typing import Type
import urllib.parse
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import RoomCreatePreset
from maubot import Plugin, MessageEvent
from maubot.handlers import command


class Config(BaseProxyConfig):

  def do_update(self, helper: ConfigUpdateHelper) -> None:
    helper.copy("api_key")
    helper.copy("whitelist")

class HolopinPlugin(Plugin):
  async def start(self) -> None:
    self.config.load_and_update()

  @command.new("holopin", require_subcommand=True)
  async def holopin(self, event: MessageEvent) -> None:
    pass    

  @holopin.subcommand(help="Issue a regular badge to a list of users")
  @command.argument("argument", pass_raw=True, required=True)
  async def issue_regular(self, event: MessageEvent, argument: str) -> None:
    await event.mark_read()

    if argument and len(argument.split()) >= 2:
      # Split input 
      argument_parts = argument.split()
      sticker_id = argument_parts[0]
      users = argument_parts[1:]
    else:
      await event.reply(f"Please provide a stickerId and at least one Matrix user that shall be awarded.")

    if event.sender in self.config["whitelist"]:
      api_key = self.config["api_key"]
      url_params = urllib.parse.urlencode({"id": sticker_id, "apiKey": api_key})
      url = "https://www.holopin.io/api/sticker/share?{}".format(url_params)
      response = await self.http.post(url, json={"email": users[0]})
      self.log.debug(f"Call {url}: {response.status} – {await response.text()}")
    else:
      await event.reply(f"You're not allowed to issue badges.")

  @classmethod
  def get_config_class(cls) -> Type[BaseProxyConfig]:
    return Config