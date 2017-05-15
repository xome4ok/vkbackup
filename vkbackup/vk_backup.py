#!/usr/bin/env python3

import argparse
import sys

from vk import Session, API

from vkbackup import vk_msg, html_backup, archive


def print_list(l):
    for x in l:
        print(x)


def main(argv):
    parser = argparse.ArgumentParser(description='Vk.com backups.')
    parser.add_argument('peer_id', type=str, help='id or screen name of user to backup')
    parser.add_argument('token', type=str, help='vk api token')
    parser.add_argument('action', choices=['json', 'text', 'audio', 'photo', 'html', 'archive'], default='text',
                        help='''json: save raw messages to json file in current directory;

                                text: output text representation of messages;

                                audio: all links to audios in messages (can be piped to wget);

                                photo: all links to photos in messages (can be piped to wget);

                                html: pretty local html with all stuff;

                                archive: downloads everything into nice folder structure
                                ''')
    args = parser.parse_args(argv)

    m = vk_msg.VkMessages(API(Session(access_token=args.token)))
    actions = {
        'text': lambda x, y: print_list(vk_msg.text_repr(x, y)),
        'json': lambda: m.save('.', args.peer_id),
        'audio': lambda x: print_list([x for x in [a.get('url', None) for a in vk_msg.audio_links(x)] if x]),
        'photo': lambda x: print_list([p['biggest'] for p in vk_msg.photo_links(x)]),
        'html': lambda x, y, z, h: html_backup.render('.', args.peer_id, x, y, z, h),
        'archive': lambda x, y, z, h: archive.make('.', args.peer_id, x, y, z, h)
    }
    action_args = []
    if not args.action == 'json':
        messages = m.get_all_from(args.peer_id)
        action_args.append(messages)
        if args.action in ('text', 'html', 'archive'):
            part = m.participants(messages)
            action_args.append(part)
        if args.action in ('html', 'archive'):
            audio_links = vk_msg.audio_links(messages)
            action_args.append(audio_links)
            photo_links = vk_msg.photo_links(messages)
            action_args.append(photo_links)
        actions[args.action](*action_args)
    else:
        actions[args.action]()


if __name__ == '__main__':
    main(sys.argv[1:])
