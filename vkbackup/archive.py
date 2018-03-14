import os

import requests
from tqdm import tqdm

from vkbackup import html_backup


def normalize_string(s):
    return s.replace(r'/', r'.')


def make(path, peer_id, msgs, participants, audio, photo):
    peer_path = os.path.join(path, peer_id)
    photo_path = os.path.join(peer_path, 'photo')
    audio_path = os.path.join(peer_path, 'audio')

    if not os.path.exists(photo_path):
        os.makedirs(photo_path)
    if not os.path.exists(audio_path):
        os.makedirs(audio_path)

    html_backup.render(peer_path, peer_id, msgs, participants, audio, photo)

    photo_links = [p['biggest'] for p in photo]
    valid_audio = [a for a in audio if a.get('url', None)]

    for link in tqdm(photo_links, desc='Downloading photos', unit='photo'):
        resp = requests.get(link, stream=True)
        filename = resp.url.rsplit('/', 1)[-1]
        file = os.path.join(photo_path, filename)
        if os.path.isfile(file):
            continue
        with open(file, 'wb') as f:
            for data in tqdm(resp.iter_content(), desc=filename, unit='b'):
                f.write(data)

    for audio_info in tqdm(valid_audio, desc='Downloading audios', unit='audio'):
        resp = requests.get(audio_info['url'], stream=True)
        filename = "{} - {}.mp3".format(audio_info['artist'], audio_info['title'][:30])  # slicing to 30 to avoid long titles
        file = os.path.join(audio_path, normalize_string(filename))
        if os.path.isfile(file):
            continue
        with open(file, 'wb') as f:
            for data in tqdm(resp.iter_content(), desc=filename, unit='b'):
                f.write(data)
