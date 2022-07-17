import getpass
import sys
from .adapters import adapter_classes, register_adapter
from .processor import process_all

from ..model.lookups import users

if len(sys.argv) != 2:
    print('Usage: botccoli <process|register>')
    sys.exit(1)

cmd = sys.argv[1]
if cmd not in ('process', 'register'):
    print(f'Unrecognized command {cmd}.')
    sys.exit(2)

if cmd == 'process':
    process_all()
    sys.exit(0)

# cmd == 'register'
users_map = users()
user_id = int(input('Romanesco user id: '))
if user_id not in users_map:
    print('Could not find user.')
    exit(3)
print(f'  --> {users_map[user_id]}')

avail_adapters = list(adapter_classes().keys())
adapter_key = input(f'Adapter type (from {",".join(avail_adapters)}): ')
if adapter_key not in avail_adapters:
    print('Could not find adapter.')
    exit(4)

user = input(f'User/login: ')
passwd = getpass.getpass()

register_adapter(user_id, adapter_key, None, None, user, passwd, None)

