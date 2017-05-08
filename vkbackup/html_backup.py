from datetime import datetime
import os
from jinja2 import Environment, PackageLoader, select_autoescape

from typing import List, Dict


def html_repr(msgs: List[Dict], participants: Dict) -> List[Dict]:
    """Html representation of conversation.

    :param msgs: messages list
    :param participants: participants dict
    :return: list of dicts with parameters to fill template
    """

    def audio_to_dict(audio) -> Dict:
        """Dict representation of audio attachment.

        :param audio: attachment of type audio
        :returns: dict with audio info
        """
        return dict(
            type='audio',
            artist=audio.get('artist') or audio.get('performer', None),
            title=audio.get('title', None),
            content_restricted='content_restricted' in audio,
            url=audio.get('url', None)
        )

    def photo_to_dict(photo) -> Dict:
        """Dict representation of photo attachment.

        :param photo: attachment of type photo
        :returns: dict with photo info
        """
        return dict(
            type='photo',
            src_big=photo.get('src_big', None),
            src_small=photo.get('src_small', None),
            src=photo.get('src', None),
            src_xbig=photo.get('src_xbig', None),
            src_xxbig=photo.get('src_xxbig', None),
            src_xxxbig=photo.get('src_xxxbig', None),
            biggest=photo.get('src_xxxbig', None) or photo.get('src_xxbig', None) or
            photo.get('src_xbig', None) or photo.get('src_big', None) or
            photo.get('src', None) or photo.get('src_small', None)
        )

    def sticker_to_dict(sticker) -> Dict:
        """Dict representation of sticker.

        :param sticker: attachment of type sticker
        :returns: dict with sticker info
        """
        return dict(
            type='sticker',
            photo_256=sticker.get('photo_256', None),  # preferable
            photo_352=sticker.get('photo_352', None),
            photo_512=sticker.get('photo_512', None),
            photo_128=sticker.get('photo_128', None),
            photo_64=sticker.get('photo_64', None),
        )

    def doc_to_dict(doc) -> Dict:
        """Dict representation of attached document.

        :param doc: attachment of type doc
        :returns: dict with doc info
        """
        return dict(
            type='doc',
            size=doc.get('size', None),
            title=doc.get('title', None),
            ext=doc.get('ext', None),
            url=doc.get('url', None)
        )

    def video_to_dict(video) -> Dict:
        """Dict representation of attached video.

        :param video: attachment of type video
        :returns: dict with video info
        """
        return dict(
            type='video',
            image=video.get('image', None),
            title=video.get('title', None)
        )

    def link_to_dict(link) -> Dict:
        """Dict representation of attached link.

        :param link: attachment of type link
        :returns: link title and link itself
        """
        return dict(
            type='link',
            title=link.get('title', None),
            url=link.get('url', None)
        )

    def wall_to_dict(wall) -> Dict:
        """Dict representation of wall post attachment

        :param wall: attachment of type wall
        :returns: dict with wall post info
        """
        attachments = wall.get('attachments', None) or []
        return dict(
            type='wall',
            text=wall.get('text', None),
            attachments=attachments_to_dicts(attachments) if attachments else None
        )

    def attachments_to_dicts(attachs: List[Dict]) -> List[Dict]:
        """Dict representation of attachments in wall post or message.

        :param attachs: non-empty attachments list
        """
        assert attachs
        attachment_funcs = dict(
            photo=photo_to_dict,
            audio=audio_to_dict,
            sticker=sticker_to_dict,
            doc=doc_to_dict,
            video=video_to_dict,
            link=link_to_dict,
            wall=wall_to_dict
        )
        return [
            attachment_funcs[x['type']](x[x['type']])
            for x in attachs
            if x['type'] in list(attachment_funcs.keys())
        ]

    def fwd_to_dict(fwd: Dict) -> Dict:
        """Dict representation of forwarded messages.

        :param fwd: message['fwd_messages']
        """
        return [
            to_dialogue(fwd_msg, 'out', participants[fwd_msg['uid']])
            for fwd_msg
            in fwd
        ]

    def to_dialogue(msg, username=None, peername=None) -> Dict:
        attachments = msg.get('attachments', None)
        return dict(
            date=str(datetime.fromtimestamp(msg['date'])),
            body=msg['body'].replace('<br>', '\n'),
            forwarded=fwd_to_dict(msg['fwd_messages']) if 'fwd_messages' in msg else None,
            attachments=attachments_to_dicts(attachments) if attachments else None,
            user=(username if 'out' in msg and msg['out'] else peername) or participants[msg['from_id']],
            is_out='out' in msg and msg['out']
        )

    return [to_dialogue(msg) for msg in msgs]


def render(path, peer_id, msgs, participants, audio, photo):
    env = Environment(
        loader=PackageLoader('vkbackup', 'templates'),
        autoescape=select_autoescape(['html'])
    )
    messages = env.get_template('layout.html')
    html = messages.render(msgs=html_repr(msgs, participants),
                           peer=peer_id,
                           participants=participants,
                           audios=audio,
                           photos=photo,
                           )
    with open(os.path.join(path, '{}.{}'.format(peer_id, 'html')), 'w', encoding='utf-8') as f:
        f.write(html)
