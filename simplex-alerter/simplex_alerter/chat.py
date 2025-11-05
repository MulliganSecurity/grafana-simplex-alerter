import pexpect
from simplex_alerter.simpx.command import ChatType
import aiofiles
from datetime import datetime
import asyncio
import pickle
from logging import getLogger
from observlib import traced

logger = getLogger(__name__)

service_name = "simpleX-alerter"

traced_conf = {
    "tracer": service_name,
}


@traced(**traced_conf)
async def get_groups(group_data):
    groups = {}
    if len(group_data["groups"]) > 0:
        for group_data_entry in group_data["groups"]:
            if "groupProfile" in group_data_entry[0]:
                groups[group_data_entry[0]["groupProfile"]["displayName"]] = (
                    group_data_entry[0]["groupId"]
                )
    return groups


@traced(**traced_conf)
def init_chat(profile_name, db_path):
    chat = pexpect.spawn(f"simplex-chat -y -p 7897 -d {db_path}")
    idx = chat.expect(["display name:", "Current user: .*"])
    if idx == 0:
        logger.info("configuring profile name", extra={"profile_name": profile_name})
        chat.sendline(profile_name)
        chat.expect("Current user: .*")
        logger.info("current user filled")
    logger.info("simplex-chat db initialized")


@traced(**traced_conf)
async def deadmans_switch_notifier(liveness_info, client):
    while True:
        await asyncio.sleep(1)
        groups = await get_groups(await client.api_get_groups())
        for user, config in liveness_info.items():
            group = config["group"]
            if (
                datetime.now() > config["last_seen"] + config["alert_threshold_seconds"]
                and not config["alert_sent"]
            ):
                logger.info(
                    f"{user} has been inactive for more than the threshold, sending alert"
                )
                chatId = groups.get(config["group"])
                if not chatId:
                    logger.error(
                        f"couldn't send the alert to {group} for user {user}: group is not connected"
                    )
                else:
                    await client.api_send_text_message(
                        ChatType.Group, chatId, config["trigger_message"]
                    )
                    config["alert_sent"] = True

            if (
                datetime.now()
                > config["last_seen"] + config["trigger_threshold_seconds"]
                and not config["switch_triggered"]
            ):
                chatId = groups.get(config["group"])
                if not chatId:
                    logger.error(
                        f"couldn't send the alert to {group} for user {user} MIA: group is not connected"
                    )
                else:
                    try:
                        await client.api_send_file(
                            ChatType.Group, chatId, config["inheritance_filepath"], config["inheritance_message"]
                        )
                        config["switch_triggered"] = True
                        logger.info(
                            f"{user} has been inactive in {group} beyond the threshold, sent message"
                        )
                    except Exception as ex:
                        logger.error(f"error delivering file: {ex}")


@traced(**traced_conf)
async def monitor_channels(liveness_info, msg_data, client):
    data_path = "/alerterconfig/ddms.pickle"
    while True:
        msg = await client.msg_q.dequeue()
        if msg["type"] == "newChatItems":
            for item in msg["chatItems"]:
                try:
                    group = item["chatInfo"]["groupInfo"]["groupProfile"]["displayName"]
                    member = item["chatItem"]["chatDir"]["groupMember"][
                        "memberProfile"
                    ]["displayName"]

                    if group not in msg_data["groups"]:
                        msg_data["groups"][group] = 1
                    else:
                        msg_data["groups"][group] += 1

                    liveness = liveness_info.get(member)

                    if liveness:
                        if member not in msg_data["users"]:
                            msg_data["users"][member] = {group: 1}
                        else:
                            msg_data["users"][member][group] += 1

                    if liveness and group == liveness["group"]:
                        liveness["last_seen"] = datetime.now()
                        pickled = pickle.dumps(liveness_info)
                        async with aiofiles.open(data_path, "wb") as fh:
                            await fh.write(pickled)
                        logger.info(
                            f"recorded liveness for user {member} in group {group}"
                        )
                        liveness["alert_sent"] = False
                        if liveness["switch_triggered"]:
                            logger.warn(
                                f"{member} has come back in {group} but MIA transmission has already been executed. Reseting"
                            )
                            liveness["switch_triggered"] = False
                except Exception as ex:
                    logger.debug(f"no associated liveness info for user: {ex}")
