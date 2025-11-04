import pexpect
import base64
from simplex_alerter.simpx.command import ChatType
import aiofiles
from datetime import datetime
import asyncio
import pickle
import json
from logging import getLogger

logger = getLogger(__name__)

def init_chat(profile_name,db_path):
    chat = pexpect.spawn(f"simplex-chat -y -p 7897 -d {db_path}")
    idx = chat.expect(["display name:", "Current user: .*"])
    if idx == 0:
        logger.info("configuring profile name", extra = {"profile_name":profile_name})
        chat.sendline(profile_name)
        chat.expect("Current user: .*")
        logger.info("current user filled")
    logger.info("simplex-chat db initialized")

async def deadmans_switch_notifier(liveness_info, client):
    while True:
        await asyncio.sleep(1)
        groups = await get_groups(await client.api_get_groups())
        for user,config in liveness_info.items():
            if datetime.now() > config["last_seen"] + config["alert_threshold_seconds"] and not config["alert_sent"]:
                logger.info(f"{user} has been inactive for more than the threshold, sending alert")
                chatId = groups.get(config["group"])
                if not chatId:
                    logger.error(f"couldn't send the alert to {group} for user {user}: group is not connected")
                else:
                    await client.api_send_text_message(ChatType.Group,chatId,config["trigger_message"])
                    config["alert_sent"] = True

            if datetime.now() > config["last_seen"] + config["trigger_threshold_seconds"] and not config["switch_triggered"]:

                chatId = groups.get(config["group"])
                if not chatId:
                    logger.error(f"couldn't send the alert to {group} for user {user} MIA: group is not connected")
                else:
                    try:
                        async with aiofiles.open(config["delivered_filepath"],"rb") as fh
                            file_content = await fh.read()
                            file_txt = base64.b64encode(file_content)
                            await client.api_send_file(ChatType.Group, chatId, file_txt)
                    config["switch_triggered"] = True
                pass #send trigger notification


async def monitor_channels(liveness_info, client):

    data_path = "/alerterconfig/ddms.pickle"
    while True:
        msg = await client.msg_q.dequeue()
        if msg["type"] == "newChatItems":
            for item in msg["chatItems"]:
                try:
                    group = item["chatInfo"]["groupInfo"]["groupProfile"]["displayName"]
                    member = item["chatItem"]["chatDir"]["groupMember"]["memberProfile"]["displayName"]
                    liveness = liveness_info.get(member)
                    if liveness and group == liveness["group"]:
                        liveness["last_seen"] = datetime.now()
                        pickled = pickle.dumps(liveness_info)
                        async with aiofiles.open(data_path,"wb") as fh:
                            await fh.write(pickled)
                        logger.info(f"recorded liveness for user {member} in group {group}")
                except Exception as ex:
                    logger.debug(f"no associated liveness info for user: {ex}")
