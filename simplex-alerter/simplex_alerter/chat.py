import pexpect
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

async def monitor_channels(config, client):
    while True:
        msg = await client.msg_q.dequeue()
        print(f"received: {msg}")
