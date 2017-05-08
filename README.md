# vkbackup
backing up data from vk.com

```
$ vkbackup -h
usage: vkbackup [-h] peer_id token {json,text,html,audio,photo}

Vk.com backups.

positional arguments:
  peer_id               id or screen name of user to backup
  token                 vk api token
  {json,text,html,audio,photo}
                        json: save raw messages to json file in current
                        directory; 
                        text: output text representation of
                        messages; 
                        audio: all links to audios in messages (can
                        be piped to wget); 
                        photo: all links to photos in
                        messages (can be piped to wget);
                        html: pretty local html with all stuff;

optional arguments:
  -h, --help            show this help message and exit
  ```

token is obtained from vk.com - https://vk.com/dev/authcode_flow_user

Installation: ```git clone https://github.com/xome4ok/vkbackup && cd vkbackup && pip install .```
