from setuptools import setup

setup(name='vkbackup',
      version='0.1',
      description='Backing up data from vk.com in CLI',
      url='http://github.com/xome4ok/vkbackup',
      author='xome4ok',
      author_email='xome4ok.ekb@gmail.com',
      license='MIT',
      packages=['vkbackup'],
      zip_safe=False,
      scripts=['bin/vkbackup'],
      requires=['jinja2', 'typing', 'vk'])
