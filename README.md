# vkbackup
backing up data from vk.com

```
$ vkbackup -h
usage: vkbackup [-h] peer_id token {json,text,audio,photo,html,archive}

Vk.com backups.

positional arguments:
  peer_id               id or screen name of user to backup
  token                 vk api token
  {json,text,audio,photo,html,archive}
                        json: save raw messages to json file in current directory; 
                        
                        text: output text representation of messages; 
                        
                        audio: all links to audios in messages (can be piped to wget); 
                        
                        photo: all links to photos in messages (can be piped to wget); 
                        
                        html: pretty local html with all stuff; 
                        
                        archive: downloads everything into nice folder structure

optional arguments:
  -h, --help            show this help message and exit
  ```

token is obtained from vk.com like this ```https://oauth.vk.com/authorize?client_id={app_id}&display=page&redirect_uri=vk.com&callback&scope=messages&response_type=token&v=5.64``` 
(for detailed information address https://vk.com/dev/authcode_flow_user)

Installation: ```git clone https://github.com/xome4ok/vkbackup && cd vkbackup && pip install .```

Downloading photos with wget: ```vkbackup $USERNAME $TOKEN photo > $USERNAME_photo_urls && wget -i $USERNAME_photo_urls```
