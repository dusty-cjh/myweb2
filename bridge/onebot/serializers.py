from common.utils.serializer import FrozenJson


class OneBotSender(FrozenJson):
    user_id: int
    nickname: str
    sex: str
    age: int

    # only for group
    card: str   # group card
    area: str
    level: str
    role: str
    title: str


class OneBotAnonymous:
    id: int
    name: str
    flag: str


class OneBotFile:
    id: str
    name: str
    size: int
    busid: int

    url: str


class OneBotEvent(FrozenJson):
    time: int
    self_id: int
    post_type: str
    message_type: str
    sub_type: str
    temp_source: int
    message_id: int
    user_id: int
    message: str
    raw_message: str
    font: int
    sender: OneBotSender

    group_id: int
    anonymous: OneBotAnonymous

    notice_type: str
    file: OneBotFile

    operator_id: int

    # pin user
    sender_id: int
    target_id: int

    honor_type: str

    card_new: str
    card_old: str

    request_type: str
    comment: str


class OneBotApiResponse(FrozenJson):
    status: str
    retcode: int
    msg: str
    wording: str
    data: dict
    echo: dict


class GetGroupInfoResponse(FrozenJson):
    group_id: int
    group_name: str
    group_memo: str
    group_create_time: int
    group_level: int
    member_count: int
    max_member_count: int

