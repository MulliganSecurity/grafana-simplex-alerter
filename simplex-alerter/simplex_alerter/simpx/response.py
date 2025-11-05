from typing import Union, List, Optional, Dict, Any, Literal, TypedDict
from enum import Enum
from datetime import datetime

from .command import (
    ChatItemId,
    MsgContent,
    DeleteMode,
    Profile,
    GroupMemberRole,
    LocalProfile,
    ServerProtocol,
    ServerCfg,
)


class ChatInfoType(str, Enum):
    """Type of chat information."""

    Direct = "direct"
    Group = "group"
    ContactRequest = "contactRequest"


class ChatResponseTag(str, Enum):
    """Tags for chat responses."""

    activeUser = "activeUser"
    usersList = "usersList"
    chatStarted = "chatStarted"
    chatRunning = "chatRunning"
    chatStopped = "chatStopped"
    apiChats = "apiChats"
    apiChat = "apiChat"
    apiParsedMarkdown = "apiParsedMarkdown"
    userProtoServers = "userProtoServers"
    contactInfo = "contactInfo"
    groupMemberInfo = "groupMemberInfo"
    newChatItems = "newChatItems"
    chatItemStatusUpdated = "chatItemStatusUpdated"
    chatItemUpdated = "chatItemUpdated"
    chatItemDeleted = "chatItemDeleted"
    msgIntegrityError = "msgIntegrityError"
    cmdOk = "cmdOk"
    userContactLink = "userContactLink"
    userContactLinkUpdated = "userContactLinkUpdated"
    userContactLinkCreated = "userContactLinkCreated"
    userContactLinkDeleted = "userContactLinkDeleted"
    contactRequestRejected = "contactRequestRejected"
    userProfile = "userProfile"
    userProfileNoChange = "userProfileNoChange"
    userProfileUpdated = "userProfileUpdated"
    contactAliasUpdated = "contactAliasUpdated"
    invitation = "invitation"
    sentConfirmation = "sentConfirmation"
    sentInvitation = "sentInvitation"
    contactUpdated = "contactUpdated"
    contactsMerged = "contactsMerged"
    contactDeleted = "contactDeleted"
    chatCleared = "chatCleared"
    receivedContactRequest = "receivedContactRequest"
    acceptingContactRequest = "acceptingContactRequest"
    contactAlreadyExists = "contactAlreadyExists"
    contactRequestAlreadyAccepted = "contactRequestAlreadyAccepted"
    contactConnecting = "contactConnecting"
    contactConnected = "contactConnected"
    contactAnotherClient = "contactAnotherClient"
    contactSubError = "contactSubError"
    contactSubSummary = "contactSubSummary"
    contactsDisconnected = "contactsDisconnected"
    contactsSubscribed = "contactsSubscribed"
    hostConnected = "hostConnected"
    hostDisconnected = "hostDisconnected"
    groupEmpty = "groupEmpty"
    memberSubError = "memberSubError"
    memberSubSummary = "memberSubSummary"
    groupSubscribed = "groupSubscribed"
    rcvFileAccepted = "rcvFileAccepted"
    rcvFileAcceptedSndCancelled = "rcvFileAcceptedSndCancelled"
    rcvFileStart = "rcvFileStart"
    rcvFileComplete = "rcvFileComplete"
    rcvFileCancelled = "rcvFileCancelled"
    rcvFileSndCancelled = "rcvFileSndCancelled"
    sndFileStart = "sndFileStart"
    sndFileComplete = "sndFileComplete"
    sndFileCancelled = "sndFileCancelled"
    sndFileRcvCancelled = "sndFileRcvCancelled"
    sndGroupFileCancelled = "sndGroupFileCancelled"
    fileTransferStatus = "fileTransferStatus"
    sndFileSubError = "sndFileSubError"
    rcvFileSubError = "rcvFileSubError"
    pendingSubSummary = "pendingSubSummary"
    groupCreated = "groupCreated"
    groupMembers = "groupMembers"
    userAcceptedGroupSent = "userAcceptedGroupSent"
    userDeletedMember = "userDeletedMember"
    sentGroupInvitation = "sentGroupInvitation"
    leftMemberUser = "leftMemberUser"
    groupDeletedUser = "groupDeletedUser"
    groupInvitation = "groupInvitation"
    receivedGroupInvitation = "receivedGroupInvitation"
    userJoinedGroup = "userJoinedGroup"
    joinedGroupMember = "joinedGroupMember"
    joinedGroupMemberConnecting = "joinedGroupMemberConnecting"
    connectedToGroupMember = "connectedToGroupMember"
    deletedMember = "deletedMember"
    deletedMemberUser = "deletedMemberUser"
    leftMember = "leftMember"
    groupRemoved = "groupRemoved"
    groupDeleted = "groupDeleted"
    groupUpdated = "groupUpdated"
    userContactLinkSubscribed = "userContactLinkSubscribed"
    userContactLinkSubError = "userContactLinkSubError"
    newContactConnection = "newContactConnection"
    contactConnectionDeleted = "contactConnectionDeleted"
    messageError = "messageError"
    chatCmdError = "chatCmdError"
    chatError = "chatError"


# Base classes for responses
class CR(TypedDict):
    """Base class for chat responses."""

    type: str


class User(TypedDict):
    """User information."""

    userId: int
    agentUserId: str
    userContactId: int
    localDisplayName: str
    profile: LocalProfile
    activeUser: bool
    viewPwdHash: str
    showNtfs: bool


class Connection(TypedDict):
    """Connection information."""

    connId: int


class ConnectionStats(TypedDict, total=False):
    """Statistics about a connection."""

    rcvServers: Optional[List[str]]
    sndServers: Optional[List[str]]


class Contact(TypedDict):
    """Contact information."""

    contactId: int
    localDisplayName: str
    profile: Profile
    activeConn: Connection
    viaGroup: Optional[int]
    createdAt: datetime


class ContactRef(TypedDict):
    """Reference to a contact."""

    contactId: int
    localDisplayName: str


class UserContactRequest(TypedDict):
    """Contact request information."""

    contactRequestId: int
    localDisplayName: str
    profile: Profile
    createdAt: datetime


class GroupProfile(TypedDict):
    """Group profile information."""

    displayName: str
    fullName: str
    image: Optional[str]


class GroupMember(TypedDict, total=False):
    """Group member information."""

    groupMemberId: int
    memberId: str
    memberRole: GroupMemberRole
    localDisplayName: str
    memberProfile: Profile
    memberContactId: Optional[int]
    activeConn: Optional[Connection]


class GroupInfo(TypedDict):
    """Group information."""

    groupId: int
    localDisplayName: str
    groupProfile: GroupProfile
    membership: GroupMember
    createdAt: datetime


class Group(TypedDict):
    """Group with members information."""

    groupInfo: GroupInfo
    members: List[GroupMember]


class UserContactLink(TypedDict, total=False):
    """User contact link information."""

    connReqContact: str
    autoAccept: Optional[Dict[str, Any]]


class PendingContactConnection(TypedDict):
    """Pending contact connection."""

    pass


class IChatInfo(TypedDict):
    """Base class for chat info."""

    type: str


class CInfoDirect(IChatInfo):
    """Direct chat info."""

    type: Literal["direct"]
    contact: Contact


class CInfoGroup(IChatInfo):
    """Group chat info."""

    type: Literal["group"]
    groupInfo: GroupInfo


class CInfoContactRequest(IChatInfo):
    """Contact request chat info."""

    type: Literal["contactRequest"]
    contactRequest: UserContactRequest


# Union type for chat info
ChatInfo = Union[CInfoDirect, CInfoGroup, CInfoContactRequest]


class ChatStats(TypedDict):
    """Chat statistics."""

    unreadCount: int
    minUnreadItemId: int


class ICIDirection(TypedDict):
    """Base class for chat item direction."""

    type: str


class CIDirectSnd(ICIDirection):
    """Direct send direction."""

    type: Literal["directSnd"]


class CIDirectRcv(ICIDirection):
    """Direct receive direction."""

    type: Literal["directRcv"]


class CIGroupSnd(ICIDirection):
    """Group send direction."""

    type: Literal["groupSnd"]


class CIGroupRcv(ICIDirection):
    """Group receive direction."""

    type: Literal["groupRcv"]
    groupMember: GroupMember


# Union type for chat item direction
CIDirection = Union[CIDirectSnd, CIDirectRcv, CIGroupSnd, CIGroupRcv]


class ICIStatus(TypedDict):
    """Base class for chat item status."""

    type: str


class CISndNew(ICIStatus):
    """New send status."""

    type: Literal["sndNew"]


class CISndSent(ICIStatus):
    """Sent status."""

    type: Literal["sndSent"]


class CISndErrorAuth(ICIStatus):
    """Auth error status."""

    type: Literal["sndErrorAuth"]


class CISndError(ICIStatus):
    """Send error status."""

    type: Literal["sndError"]
    agentError: Dict[str, Any]  # AgentErrorType


class CIRcvNew(ICIStatus):
    """New receive status."""

    type: Literal["rcvNew"]


class CIRcvRead(ICIStatus):
    """Read status."""

    type: Literal["rcvRead"]


# Union type for chat item status
CIStatus = Union[CISndNew, CISndSent, CISndErrorAuth, CISndError, CIRcvNew, CIRcvRead]


class FormattedText(TypedDict):
    """Formatted text."""

    pass


class CIMeta(TypedDict):
    """Chat item metadata."""

    itemId: ChatItemId
    itemTs: datetime
    itemText: str
    itemStatus: CIStatus
    createdAt: datetime
    itemDeleted: bool
    itemEdited: bool
    editable: bool


class CIQuote(TypedDict, total=False):
    """Quote in a chat item."""

    chatDir: Optional[CIDirection]
    itemId: Optional[int]
    sharedMsgId: Optional[str]
    sentAt: datetime
    content: MsgContent
    formattedText: Optional[List[FormattedText]]


class ICIContent(TypedDict):
    """Base class for chat item content."""

    type: str


class CISndMsgContent(ICIContent):
    """Send message content."""

    type: Literal["sndMsgContent"]
    msgContent: MsgContent


class CIRcvMsgContent(ICIContent):
    """Receive message content."""

    type: Literal["rcvMsgContent"]
    msgContent: MsgContent


class CISndDeleted(ICIContent):
    """Send deleted content."""

    type: Literal["sndDeleted"]
    deleteMode: DeleteMode


class CIRcvDeleted(ICIContent):
    """Receive deleted content."""

    type: Literal["rcvDeleted"]
    deleteMode: DeleteMode


class RcvFileTransfer(TypedDict, total=False):
    """Receive file transfer information."""

    fileId: int
    senderDisplayName: str
    chunkSize: int
    cancelled: bool
    grpMemberId: Optional[int]


class SndFileTransfer(TypedDict):
    """Send file transfer information."""

    fileId: int
    fileName: str
    filePath: str
    fileSize: int
    chunkSize: int
    recipientDisplayName: str
    connId: int


class FileTransferMeta(TypedDict):
    """File transfer metadata."""

    fileId: int
    fileName: str
    filePath: str
    fileSize: int
    chunkSize: int
    cancelled: bool


class CISndFileInvitation(ICIContent):
    """Send file invitation content."""

    type: Literal["sndFileInvitation"]
    fileId: int
    filePath: str


class CIRcvFileInvitation(ICIContent):
    """Receive file invitation content."""

    type: Literal["rcvFileInvitation"]
    rcvFileTransfer: RcvFileTransfer


# Union type for chat item content
CIContent = Union[
    CISndMsgContent,
    CIRcvMsgContent,
    CISndDeleted,
    CIRcvDeleted,
    CISndFileInvitation,
    CIRcvFileInvitation,
]


class ChatItem(TypedDict, total=False):
    """Chat item."""

    chatDir: CIDirection
    meta: CIMeta
    content: CIContent
    formattedText: Optional[List[FormattedText]]
    quotedItem: Optional[CIQuote]


class AChatItem(TypedDict):
    """Chat item with chat info."""

    chatInfo: ChatInfo
    chatItem: ChatItem


class Chat(TypedDict):
    """Chat with items and stats."""

    chatInfo: ChatInfo
    chatItems: List[ChatItem]
    chatStats: ChatStats


class UserProtoServers(TypedDict):
    """User protocol servers."""

    serverProtocol: ServerProtocol
    protoServers: List[ServerCfg]
    presetServers: str


class UserInfo(TypedDict):
    """User information with unread count."""

    user: User
    unreadCount: int


class IChatError(TypedDict):
    """Base class for chat errors."""

    type: str


class ChatErrorType(TypedDict):
    """Chat error type."""

    type: str


class CENoActiveUser(ChatErrorType):
    """No active user error."""

    type: Literal["noActiveUser"]


class CEActiveUserExists(ChatErrorType):
    """Active user exists error."""

    type: Literal["activeUserExists"]


class ChatErrorChat(IChatError):
    """Chat error."""

    type: Literal["error"]
    errorType: ChatErrorType


class ChatErrorAgent(IChatError):
    """Agent error."""

    type: Literal["errorAgent"]
    agentError: Dict[str, Any]  # AgentErrorType


class ChatErrorStore(IChatError):
    """Store error."""

    type: Literal["errorStore"]
    storeError: Dict[str, Any]  # StoreErrorType


# Union type for chat errors
ChatError = Union[ChatErrorChat, ChatErrorAgent, ChatErrorStore]


class MsgErrorType(TypedDict):
    """Message error type."""

    pass


class MemberSubStatus(TypedDict, total=False):
    """Member subscription status."""

    member: GroupMember
    memberError: Optional[ChatError]


class ContactSubStatus(TypedDict):
    """Contact subscription status."""

    pass


class PendingSubStatus(TypedDict):
    """Pending subscription status."""

    pass


# Response type definitions
class CRActiveUser(CR):
    """Active user response."""

    type: Literal["activeUser"]
    user: User


class CRUsersList(CR):
    """Users list response."""

    type: Literal["usersList"]
    users: List[UserInfo]


class CRChatStarted(CR):
    """Chat started response."""

    type: Literal["chatStarted"]


class CRChatRunning(CR):
    """Chat running response."""

    type: Literal["chatRunning"]


class CRChatStopped(CR):
    """Chat stopped response."""

    type: Literal["chatStopped"]


class CRApiChats(CR):
    """API chats response."""

    type: Literal["apiChats"]
    user: User
    chats: List[Chat]


class CRApiChat(CR):
    """API chat response."""

    type: Literal["apiChat"]
    user: User
    chat: Chat


class CRApiParsedMarkdown(CR):
    """API parsed markdown response."""

    type: Literal["apiParsedMarkdown"]
    formattedText: Optional[List[FormattedText]]


class CRUserProtoServers(CR):
    """User protocol servers response."""

    type: Literal["userProtoServers"]
    user: User
    servers: UserProtoServers


class CRContactInfo(CR):
    """Contact info response."""

    type: Literal["contactInfo"]
    user: User
    contact: Contact
    connectionStats: ConnectionStats
    customUserProfile: Optional[Profile]


class CRGroupMemberInfo(CR):
    """Group member info response."""

    type: Literal["groupMemberInfo"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember
    connectionStats_: Optional[ConnectionStats]


class CRNewChatItems(CR):
    """New chat items response."""

    type: Literal["newChatItems"]
    user: User
    chatItems: List[AChatItem]


class CRChatItemStatusUpdated(CR):
    """Chat item status updated response."""

    type: Literal["chatItemStatusUpdated"]
    user: User
    chatItem: AChatItem


class CRChatItemUpdated(CR):
    """Chat item updated response."""

    type: Literal["chatItemUpdated"]
    user: User
    chatItem: AChatItem


class CRChatItemDeleted(CR):
    """Chat item deleted response."""

    type: Literal["chatItemDeleted"]
    user: User
    deletedChatItem: AChatItem
    toChatItem: Optional[AChatItem]
    byUser: bool


class CRMsgIntegrityError(CR):
    """Message integrity error response."""

    type: Literal["msgIntegrityError"]
    user: User
    msgError: MsgErrorType


class CRCmdOk(CR):
    """Command OK response."""

    type: Literal["cmdOk"]
    user_: Optional[User]


class CRUserContactLink(CR):
    """User contact link response."""

    type: Literal["userContactLink"]
    user: User
    contactLink: UserContactLink


class CRUserContactLinkUpdated(CR):
    """User contact link updated response."""

    type: Literal["userContactLinkUpdated"]
    user: User
    connReqContact: str
    autoAccept: bool
    autoReply: Optional[MsgContent]


class CRUserContactLinkCreated(CR):
    """User contact link created response."""

    type: Literal["userContactLinkCreated"]
    user: User
    connReqContact: str


class CRUserContactLinkDeleted(CR):
    """User contact link deleted response."""

    type: Literal["userContactLinkDeleted"]
    user: User


class CRContactRequestRejected(CR):
    """Contact request rejected response."""

    type: Literal["contactRequestRejected"]
    user: User
    contactRequest: UserContactRequest


class CRUserProfile(CR):
    """User profile response."""

    type: Literal["userProfile"]
    user: User
    profile: Profile


class CRUserProfileNoChange(CR):
    """User profile no change response."""

    type: Literal["userProfileNoChange"]
    user: User


class CRUserProfileUpdated(CR):
    """User profile updated response."""

    type: Literal["userProfileUpdated"]
    user: User
    fromProfile: Profile
    toProfile: Profile


class CRContactAliasUpdated(CR):
    """Contact alias updated response."""

    type: Literal["contactAliasUpdated"]
    user: User
    toContact: Contact


class CRInvitation(CR):
    """Invitation response."""

    type: Literal["invitation"]
    user: User
    connReqInvitation: str


class CRSentConfirmation(CR):
    """Sent confirmation response."""

    type: Literal["sentConfirmation"]
    user: User


class CRSentInvitation(CR):
    """Sent invitation response."""

    type: Literal["sentInvitation"]
    user: User


class CRContactUpdated(CR):
    """Contact updated response."""

    type: Literal["contactUpdated"]
    user: User
    fromContact: Contact
    toContact: Contact


class CRContactsMerged(CR):
    """Contacts merged response."""

    type: Literal["contactsMerged"]
    user: User
    intoContact: Contact
    mergedContact: Contact


class CRContactDeleted(CR):
    """Contact deleted response."""

    type: Literal["contactDeleted"]
    user: User
    contact: Contact


class CRChatCleared(CR):
    """Chat cleared response."""

    type: Literal["chatCleared"]
    user: User
    chatInfo: ChatInfo


class CRReceivedContactRequest(CR):
    """Received contact request response."""

    type: Literal["receivedContactRequest"]
    user: User
    contactRequest: UserContactRequest


class CRAcceptingContactRequest(CR):
    """Accepting contact request response."""

    type: Literal["acceptingContactRequest"]
    user: User
    contact: Contact


class CRContactAlreadyExists(CR):
    """Contact already exists response."""

    type: Literal["contactAlreadyExists"]
    user: User
    contact: Contact


class CRContactRequestAlreadyAccepted(CR):
    """Contact request already accepted response."""

    type: Literal["contactRequestAlreadyAccepted"]
    user: User
    contact: Contact


class CRContactConnecting(CR):
    """Contact connecting response."""

    type: Literal["contactConnecting"]
    user: User
    contact: Contact


class CRContactConnected(CR):
    """Contact connected response."""

    type: Literal["contactConnected"]
    contact: Contact
    user: User
    userCustomProfile: Optional[Profile]


class CRContactAnotherClient(CR):
    """Contact another client response."""

    type: Literal["contactAnotherClient"]
    user: User
    contact: Contact


class CRContactSubError(CR):
    """Contact subscription error response."""

    type: Literal["contactSubError"]
    user: User
    contact: Contact
    chatError: ChatError


class CRContactSubSummary(CR):
    """Contact subscription summary response."""

    type: Literal["contactSubSummary"]
    user: User
    contactSubscriptions: List[ContactSubStatus]


class CRContactsDisconnected(CR):
    """Contacts disconnected response."""

    type: Literal["contactsDisconnected"]
    user: User
    server: str
    contactRefs: List[ContactRef]


class CRContactsSubscribed(CR):
    """Contacts subscribed response."""

    type: Literal["contactsSubscribed"]
    user: User
    server: str
    contactRefs: List[ContactRef]


class CRHostConnected(CR):
    """Host connected response."""

    type: Literal["hostConnected"]
    protocol: str
    transportHost: str


class CRHostDisconnected(CR):
    """Host disconnected response."""

    type: Literal["hostDisconnected"]
    protocol: str
    transportHost: str


class CRGroupEmpty(CR):
    """Group empty response."""

    type: Literal["groupEmpty"]
    user: User
    groupInfo: GroupInfo


class CRMemberSubError(CR):
    """Member subscription error response."""

    type: Literal["memberSubError"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember
    chatError: ChatError


class CRMemberSubSummary(CR):
    """Member subscription summary response."""

    type: Literal["memberSubSummary"]
    user: User
    memberSubscriptions: List[MemberSubStatus]


class CRGroupSubscribed(CR):
    """Group subscribed response."""

    type: Literal["groupSubscribed"]
    user: User
    groupInfo: GroupInfo


class CRRcvFileAccepted(CR):
    """Receive file accepted response."""

    type: Literal["rcvFileAccepted"]
    user: User
    chatItem: AChatItem


class CRRcvFileAcceptedSndCancelled(CR):
    """Receive file accepted sender cancelled response."""

    type: Literal["rcvFileAcceptedSndCancelled"]
    user: User
    rcvFileTransfer: RcvFileTransfer


class CRRcvFileStart(CR):
    """Receive file start response."""

    type: Literal["rcvFileStart"]
    user: User
    chatItem: AChatItem


class CRRcvFileComplete(CR):
    """Receive file complete response."""

    type: Literal["rcvFileComplete"]
    user: User
    chatItem: AChatItem


class CRRcvFileCancelled(CR):
    """Receive file cancelled response."""

    type: Literal["rcvFileCancelled"]
    user: User
    rcvFileTransfer: RcvFileTransfer


class CRRcvFileSndCancelled(CR):
    """Receive file sender cancelled response."""

    type: Literal["rcvFileSndCancelled"]
    user: User
    rcvFileTransfer: RcvFileTransfer


class CRSndFileStart(CR):
    """Send file start response."""

    type: Literal["sndFileStart"]
    user: User
    chatItem: AChatItem
    sndFileTransfer: SndFileTransfer


class CRSndFileComplete(CR):
    """Send file complete response."""

    type: Literal["sndFileComplete"]
    user: User
    chatItem: AChatItem
    sndFileTransfer: SndFileTransfer


class CRSndFileCancelled(CR):
    """Send file cancelled response."""

    type: Literal["sndFileCancelled"]
    user: User
    chatItem: AChatItem
    sndFileTransfer: SndFileTransfer


class CRSndFileRcvCancelled(CR):
    """Send file receiver cancelled response."""

    type: Literal["sndFileRcvCancelled"]
    user: User
    chatItem: AChatItem
    sndFileTransfer: SndFileTransfer


class CRSndGroupFileCancelled(CR):
    """Send group file cancelled response."""

    type: Literal["sndGroupFileCancelled"]
    user: User
    chatItem: AChatItem
    fileTransferMeta: FileTransferMeta
    sndFileTransfers: List[SndFileTransfer]


class CRSndFileSubError(CR):
    """Send file subscription error response."""

    type: Literal["sndFileSubError"]
    user: User
    sndFileTransfer: SndFileTransfer
    chatError: ChatError


class CRRcvFileSubError(CR):
    """Receive file subscription error response."""

    type: Literal["rcvFileSubError"]
    user: User
    rcvFileTransfer: RcvFileTransfer
    chatError: ChatError


class CRPendingSubSummary(CR):
    """Pending subscription summary response."""

    type: Literal["pendingSubSummary"]
    user: User
    pendingSubStatus: List[PendingSubStatus]


class CRGroupCreated(CR):
    """Group created response."""

    type: Literal["groupCreated"]
    user: User
    groupInfo: GroupInfo


class CRGroupMembers(CR):
    """Group members response."""

    type: Literal["groupMembers"]
    user: User
    group: Group


class CRUserAcceptedGroupSent(CR):
    """User accepted group sent response."""

    type: Literal["userAcceptedGroupSent"]
    user: User
    groupInfo: GroupInfo
    hostContact: Optional[Contact]


class CRUserDeletedMember(CR):
    """User deleted member response."""

    type: Literal["userDeletedMember"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRSentGroupInvitation(CR):
    """Sent group invitation response."""

    type: Literal["sentGroupInvitation"]
    user: User
    groupInfo: GroupInfo
    contact: Contact
    member: GroupMember


class CRLeftMemberUser(CR):
    """Left member user response."""

    type: Literal["leftMemberUser"]
    user: User
    groupInfo: GroupInfo


class CRGroupDeletedUser(CR):
    """Group deleted user response."""

    type: Literal["groupDeletedUser"]
    user: User
    groupInfo: GroupInfo


class CRGroupInvitation(CR):
    """Group invitation response."""

    type: Literal["groupInvitation"]
    user: User
    groupInfo: GroupInfo


class CRReceivedGroupInvitation(CR):
    """Received group invitation response."""

    type: Literal["receivedGroupInvitation"]
    user: User
    groupInfo: GroupInfo
    contact: Contact
    memberRole: GroupMemberRole


class CRUserJoinedGroup(CR):
    """User joined group response."""

    type: Literal["userJoinedGroup"]
    user: User
    groupInfo: GroupInfo
    hostMember: GroupMember


class CRJoinedGroupMember(CR):
    """Joined group member response."""

    type: Literal["joinedGroupMember"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRJoinedGroupMemberConnecting(CR):
    """Joined group member connecting response."""

    type: Literal["joinedGroupMemberConnecting"]
    user: User
    groupInfo: GroupInfo
    hostMember: GroupMember
    member: GroupMember


class CRConnectedToGroupMember(CR):
    """Connected to group member response."""

    type: Literal["connectedToGroupMember"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRDeletedMember(CR):
    """Deleted member response."""

    type: Literal["deletedMember"]
    user: User
    groupInfo: GroupInfo
    byMember: GroupMember
    deletedMember: GroupMember


class CRDeletedMemberUser(CR):
    """Deleted member user response."""

    type: Literal["deletedMemberUser"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRLeftMember(CR):
    """Left member response."""

    type: Literal["leftMember"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRGroupRemoved(CR):
    """Group removed response."""

    type: Literal["groupRemoved"]
    user: User
    groupInfo: GroupInfo


class CRGroupDeleted(CR):
    """Group deleted response."""

    type: Literal["groupDeleted"]
    user: User
    groupInfo: GroupInfo
    member: GroupMember


class CRGroupUpdated(CR):
    """Group updated response."""

    type: Literal["groupUpdated"]
    user: User
    fromGroup: GroupInfo
    toGroup: GroupInfo
    member_: Optional[GroupMember]


class CRUserContactLinkSubscribed(CR):
    """User contact link subscribed response."""

    type: Literal["userContactLinkSubscribed"]


class CRUserContactLinkSubError(CR):
    """User contact link subscription error response."""

    type: Literal["userContactLinkSubError"]
    chatError: ChatError


class CRContactConnectionDeleted(CR):
    """Contact connection deleted response."""

    type: Literal["contactConnectionDeleted"]
    user: User
    connection: PendingContactConnection


class CRMessageError(CR):
    """Message error response."""

    type: Literal["messageError"]
    user: User
    severity: str
    errorMessage: str


class CRChatCmdError(CR):
    """Chat command error response."""

    type: Literal["chatCmdError"]
    user_: Optional[User]
    chatError: ChatError


class CRChatError(CR):
    """Chat error response."""

    type: Literal["chatError"]
    user_: Optional[User]
    chatError: ChatError


# Define the union type for all possible chat responses
ChatResponse = Union[
    CRActiveUser,
    CRUsersList,
    CRChatStarted,
    CRChatRunning,
    CRChatStopped,
    CRApiChats,
    CRApiChat,
    CRApiParsedMarkdown,
    CRUserProtoServers,
    CRContactInfo,
    CRGroupMemberInfo,
    CRNewChatItems,
    CRChatItemStatusUpdated,
    CRChatItemUpdated,
    CRChatItemDeleted,
    CRMsgIntegrityError,
    CRCmdOk,
    CRUserContactLink,
    CRUserContactLinkUpdated,
    CRUserContactLinkCreated,
    CRUserContactLinkDeleted,
    CRContactRequestRejected,
    CRUserProfile,
    CRUserProfileNoChange,
    CRUserProfileUpdated,
    CRContactAliasUpdated,
    CRInvitation,
    CRSentConfirmation,
    CRSentInvitation,
    CRContactUpdated,
    CRContactsMerged,
    CRContactDeleted,
    CRChatCleared,
    CRReceivedContactRequest,
    CRAcceptingContactRequest,
    CRContactAlreadyExists,
    CRContactRequestAlreadyAccepted,
    CRContactConnecting,
    CRContactConnected,
    CRContactAnotherClient,
    CRContactSubError,
    CRContactSubSummary,
    CRContactsDisconnected,
    CRContactsSubscribed,
    CRHostConnected,
    CRHostDisconnected,
    CRGroupEmpty,
    CRMemberSubError,
    CRMemberSubSummary,
    CRGroupSubscribed,
    CRRcvFileAccepted,
    CRRcvFileAcceptedSndCancelled,
    CRRcvFileStart,
    CRRcvFileComplete,
    CRRcvFileCancelled,
    CRRcvFileSndCancelled,
    CRSndFileStart,
    CRSndFileComplete,
    CRSndFileCancelled,
    CRSndFileRcvCancelled,
    CRSndGroupFileCancelled,
    CRSndFileSubError,
    CRRcvFileSubError,
    CRPendingSubSummary,
    CRGroupCreated,
    CRGroupMembers,
    CRUserAcceptedGroupSent,
    CRUserDeletedMember,
    CRSentGroupInvitation,
    CRLeftMemberUser,
    CRGroupDeletedUser,
    CRGroupInvitation,
    CRReceivedGroupInvitation,
    CRUserJoinedGroup,
    CRJoinedGroupMember,
    CRJoinedGroupMemberConnecting,
    CRConnectedToGroupMember,
    CRDeletedMember,
    CRDeletedMemberUser,
    CRLeftMember,
    CRGroupRemoved,
    CRGroupDeleted,
    CRGroupUpdated,
    CRUserContactLinkSubscribed,
    CRUserContactLinkSubError,
    CRContactConnectionDeleted,
    CRMessageError,
    CRChatCmdError,
    CRChatError,
]


def ci_content_text(content: CIContent) -> Optional[str]:
    """Extract text from chat item content."""
    if content["type"] == "sndMsgContent" or content["type"] == "rcvMsgContent":
        msg_content = content.get("msgContent", {})
        return msg_content.get("text")
    return None
