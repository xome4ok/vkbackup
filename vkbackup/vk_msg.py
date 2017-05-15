import json
import os
import time
from datetime import datetime
from typing import List, Dict, Union, Any

from vk.api import API as VKAPI
from tqdm import tqdm


def attachments_of_type(msgs: List[Dict], attach_type: str) -> List[Dict]:
    """Attachment objects of certain type. Also looks to fwd messages."""
    return [
               attach
               for msg in msgs if 'attachments' in msg
               for attach in msg['attachments'] if attach['type'] == attach_type
               ] + [
               attach
               for msg in msgs if 'fwd_messages' in msg
               for fwd_msg in msg['fwd_messages'] if 'attachments' in fwd_msg
               for attach in fwd_msg['attachments'] if attach['type'] == attach_type
               ]


def text_repr(msgs: List[Dict],
              participants: Dict,
              user_name: str = None,
              peer_name: str = None,
              date: bool = True) -> List[str]:
    """Text representation of conversation.

    :param msgs: messages list
    :param participants: participants dict
    :param user_name: name of user, which runs script
    :param peer_name: name of peer
    :return: list of dialogue lines
    """

    def audio_to_text(audio) -> str:
        """Text representation of audio attachment.

        :param audio: attachment of type audio
        :returns: string with audio info
        """
        return 'audio: {} - {}'.format(audio.get('performer') or audio.get('artist', None), audio.get('title', None))

    def photo_to_text(photo) -> str:
        """Text representation of photo attachment (link).

        :param photo: attachment of type photo
        :returns: link to photo
        """
        return 'photo: {}'.format(photo.get('src_xxxbig') or photo.get('src_big', None))

    def sticker_to_text(sticker) -> str:
        """Text representation of sticker.

        :param sticker: attachment of type sticker
        :returns: link to sticker
        """
        return 'sticker: {}'.format(sticker.get('photo_256', None))

    def doc_to_text(doc) -> str:
        """Text representation of attached document.

        :param doc: attachment of type doc
        :returns: name and link to doc
        """
        return 'doc: {} {}'.format(doc.get('title'), doc.get('url'))

    def video_to_text(video) -> str:
        """Text representation of attached video.

        :param video: attachment of type video
        :returns: name of video
        """
        return 'video: {}'.format(video.get('title', None))

    def link_to_text(link) -> str:
        """Text representation of attached link.

        :param link: attachment of type link
        :returns: link title and link itself
        """
        return 'link: {}({})'.format(link.get('title', None), link.get('url', None))

    def wall_to_text(wall) -> str:
        """Text representation of wall post attachment

        :param wall: attachment of type wall
        :returns: wall text
        """
        attachments = wall.get('attachments', None) or []
        return 'wall: {} {}'.format(
            wall.get('text', None),
            '' if not attachments else '[{}]'.format(attachments_to_text(attachments))
        )

    def attachments_to_text(attachs: List[Dict]) -> str:
        """Text representation of attachments in wall post or message.

        :param attachs: non-empty attachments list
        """
        assert attachs
        attachment_funcs = dict(photo=photo_to_text,
                                audio=audio_to_text,
                                sticker=sticker_to_text,
                                doc=doc_to_text,
                                video=video_to_text,
                                link=link_to_text,
                                wall=wall_to_text
                                )
        attachments = ', '.join([
                                    attachment_funcs[x['type']](x[x['type']])
                                    for x
                                    in attachs
                                    if x['type'] in list(attachment_funcs.keys())
                                    ])
        return '{}'.format(attachments)

    def user_full_name(user: Dict) -> str:
        """Convert user object to full name."""
        return ' '.join((user['first_name'], user['last_name']))

    def fwd_to_text(fwd):
        """Text representation of forwarded messages.

        :param fwd: message['fwd_messages']
        """
        return '\n    >' + '\n    >'.join([
                                              to_dialogue(fwd_msg,
                                                          'out',
                                                          user_full_name(participants[fwd_msg['uid']]))
                                              for fwd_msg
                                              in fwd
                                              ])

    def to_dialogue(msg, user, peer) -> str:
        attachments = msg.get('attachments', None)
        return '{}{}{}{}'.format(
            '{}{}: '.format(
                str(datetime.fromtimestamp(msg['date'])) + ' ' if date else '',
                (user if 'out' in msg and msg['out'] else peer) or user_full_name(participants[msg['from_id']])
            ),
            msg['body'],
            fwd_to_text(msg['fwd_messages']) if 'fwd_messages' in msg else '',
            ' [{}]'.format(attachments_to_text(attachments)) if attachments else ''
        )

    return [to_dialogue(msg, user_name, peer_name) for msg in msgs]


def photo_links(msgs: List[Dict]) -> List[Dict[str, Any]]:
    """Get all links to attached photos in messages.

    :param msgs: list of messages
    :return: list of links
    """
    photo_attachments = attachments_of_type(msgs, 'photo')
    return [dict(
        type='photo',
        src_big=photo['photo'].get('src_big', None),
        src_small=photo['photo'].get('src_small', None),
        src=photo['photo'].get('src', None),
        src_xbig=photo['photo'].get('src_xbig', None),
        src_xxbig=photo['photo'].get('src_xxbig', None),
        src_xxxbig=photo['photo'].get('src_xxxbig', None),
        biggest=photo['photo'].get('src_xxxbig', None) or photo['photo'].get('src_xxbig', None) or
                photo['photo'].get('src_xbig', None) or photo['photo'].get('src_big', None) or
                photo['photo'].get('src', None) or photo['photo'].get('src_small', None)
    ) for photo in photo_attachments]


def audio_links(msgs: List[Dict]) -> List[Dict[str, Any]]:
    """Get all attached audio objects in message list.

    :param msgs: list of messages:
    :return: list({name, link})
    """
    audio_attachments = attachments_of_type(msgs, 'audio')
    return [dict(
        type='audio',
        artist=audio['audio'].get('artist') or audio['audio'].get('performer', None),
        title=audio['audio'].get('title', None),
        content_restricted='content_restricted' in audio['audio'],
        url=audio['audio'].get('url', None)
    ) for audio in audio_attachments]


class VkMessages:
    """Convenient work with vk messages api."""

    def __init__(self, vkapi: VKAPI) -> None:
        """
        :param vkapi: connected vk api
        """
        self.vkapi = vkapi

    def get_all_from(self, id: Union[str, int], is_chat: bool = False) -> List[Dict]:
        """Fetches all messages from user conversation or group chat.

        :param id: chat_id or user_id or screen name
        :param is_chat: if True, user_id is treated as chat_id
        :return: list of message objects (dicts)
        """
        messages_gethistory_params = {
            'offset': '0',
            'count': '200',
            'id': id if is_chat else self.get_user(str(id))['uid'],
            'rev': '1'
        }
        all_messages = []
        n = 0
        total = (self.vkapi.messages.getHistory(chat_id=messages_gethistory_params['id'], count=0)
                if is_chat
                else self.vkapi.messages.getHistory(user_id=messages_gethistory_params['id'], count=0))[0]
        # print('Going to fetch {} messages'.format(total))
        with tqdm(desc='Downloading messages', unit='msg', total=total) as progress:
            while True:
                msg_query_part = '''API.messages.getHistory({{"offset": {offset}, "count": 200, ''' + \
                                 ('''"user_id" ''' if not is_chat else '''"chat_id" ''') + ''': {id}, "rev": {rev}}})+'''
                msg_query = 'return '
                for i in range(n, n + 4000, 200):
                    msg_query += msg_query_part.format(offset=i,
                                                       id=int(messages_gethistory_params['id']),
                                                       rev=int(messages_gethistory_params['rev']))
                msg_query = msg_query.strip('+')
                msg_query += ';'

                current_bulk = self.vkapi.execute(code=msg_query)
                time.sleep(1)

                all_messages.append(current_bulk)
                n += len(current_bulk)
                progress.update(len(current_bulk))
                # print('Inserted {} elements.\nlast: {}'.format(n, all_messages[-1][-1]))
                if type(current_bulk[-1]) is int:
                    break

        flat = [y for x in all_messages for y in x]
        cleaned = [x for x in flat if type(x) is not int]
        return cleaned

    def participants(self, msgs: List[Dict]) -> Dict[str, Dict]:
        """User info for every user in conversation including forwarded messages."""
        return {u['uid']: {key: u[key] for key in u if key != 'uid'}
                for u
                in list(map(self.get_user,
                            set(
                                [msg['uid'] for msg in msgs] +
                                [msg['from_id'] for msg in msgs] +
                                [
                                    fwd_msg['uid'] for msg in msgs if 'fwd_messages' in msg
                                    for fwd_msg in msg['fwd_messages']
                                    ]
                            )
                            ))}

    def get_user(self, user_id: Union[str, int]) -> 'User':
        """Wrapper for users.get call.

        :param user_id: screen name or id
        :return: user object with name and screen_name
        """
        time.sleep(1)
        return self.vkapi.users.get(
            user_ids=str(user_id),
            fields='name,screen_name'
        )[0]

    def save(self, path: str, user_id: Union[str, int]) -> None:
        """Save messages to json file.

        :param path: path to file, like /home/user/folder
        :param user_id: screen name or id
        """
        user = self.get_user(user_id)
        filename = '{} {} ({}).{}'.format(user['first_name'],
                                          user['last_name'],
                                          str(datetime.now().date()),
                                          'json')
        msgs = self.get_all_from(user['uid'])
        with open(os.path.join(path, filename), mode='w') as f:
            f.write(json.dumps(msgs))
