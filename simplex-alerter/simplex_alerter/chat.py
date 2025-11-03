import pexpect
from time import time
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
        for user,config in liveness_info.items():
            if time.now() > config["last_seen"] + config["alert_threshold_seconds"] and not config["alert_sent"]:
                logger.info(f"{user} has been inactive for more than the threshold, sending alert")
                config["alert_sent"] = True
                pass # send notification alert
            if time.now() > config["last_seen"] + config["trigger_threshold_seconds"] and not config["switch_triggered"]:
                config["switch_triggered"] = True
                pass #send trigger notification


async def monitor_channels(liveness_info, client):

    while True:
        msg = await client.msg_q.dequeue()
        if msg["type"] == "newChatItems":
            for item in msg["chatItems"]:
                try:
                    member = item["chatItem"]["chatDir"]["groupMember"]["localDisplayName"]
                    liveness = liveness_info.get(member)
                    if liveness:
                        liveness["last_seen"] = time.now()
                        print(f"recorded liveness for user {member}")
                except Exception as ex:
                    print(f"no associated liveness info for user: {ex}")
                    logger.debug(f"no associated liveness info for user: {ex}")
