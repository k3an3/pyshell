import atexit
import os
import readline

from queue import Queue
from threading import Thread
from time import strftime

downloads_directory = "downloads"

historyPath = os.path.expanduser("~/.pyshellhistory")
if os.path.exists(historyPath):
    readline.read_history_file(historyPath)


def save_history():
    readline.write_history_file(historyPath)


tab_complete = {}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PyShell:
    def __init__(self, handler, completion=True):
        self.handler = handler
        self.timeout = 20
        self.current_path = '/'
        self.q = Queue(5)
        readline.set_completer_delims(' /;&'"")
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self.complete)
        if completion:
            t = Thread(target=self.tab_complete_thread)
            t.setDaemon(True)
            t.start()

    def complete(self, text, state):
        tokens = readline.get_line_buffer().split()
        thistoken = tokens[-1]
        thisdir = os.path.dirname(thistoken)
        thispath = os.path.abspath(os.path.join(self.current_path, thisdir))
        if thispath != '/':
            thispath += '/'
        if thispath not in tab_complete:
            self.populate_tab_complete(thispath)
        if thispath not in tab_complete:
            return False
        suffix = [x for x in tab_complete[thispath] if x.startswith(text)][state:]
        if len(suffix):
            result = suffix[0]
            if result[-1] != '/':
                result += ' '
            return result
        return False

    def populate_tab_complete(self, path):
        global tab_complete;
        print(self.handler(20, 'bash', '-c "cd {} && ls -p"'.format(path)))
        entries = self.handler(20, 'bash', '-c "cd {} && ls -p"'.format(path)).split("\n")[:-1]
        if entries:
            tab_complete[path] = entries

    # print ("\nuse 'settimeout 30' to set the timeout to 30 seconds, etc\n")
    def tab_complete_thread(self):
        while True:
            path = self.q.get()
            if path == '>>exit<<':
                break
            self.populate_tab_complete(path)

    def run(self):
        self.q.put('/')
        while True:
            try:
                inputstr = input('{}{} {}${} '.format(
                    bcolors.OKBLUE,
                    self.current_path,
                    bcolors.WARNING,
                    bcolors.ENDC))
            except EOFError:
                self.exit_handler()
                break
            parts = inputstr.split(' ', 1)
            if len(parts) == 1:
                parts.append(' ')
            if parts[0] == 'exit':
                self.q.put('>>exit<<')
                break
            if parts[0] == 'cd':
                if parts[1] == ' ':
                    self.current_path = '/'
                else:
                    self.current_path = os.path.abspath(os.path.join(self.current_path, parts[1])).strip()
                self.q.put(self.current_path)
                continue
            if parts[0] == 'get':
                path_to_download = os.path.abspath(os.path.join(self.current_path, parts[1])).strip()
                tgz = self.handler(self.timeout, 'tar', 'cz {}'.format(path_to_download), no_decode=True)
                filename = path_to_download.replace('/', '_') + '.' + strftime("%Y%m%d%H%M%S") + '.tgz'
                if not os.path.exists(downloads_directory):
                    os.makedirs(downloads_directory)
                f = open(os.path.join(downloads_directory, filename), 'wb')
                f.write(tgz)
                f.close()
                print('Saved as {}'.format(filename))
                continue
            if parts[0] == 'settimeout':
                self.timeout = int(parts[1])
                print('Timeout set to {} seconds'.format(self.timeout))
                continue

            cmd = 'bash'
            opts = '-c "cd {} 2>&1 && {} 2>&1"'.format(self.current_path, inputstr.replace('"', '\\"'))

            result = self.handler(self.timeout, cmd, opts)
            print("{}{}".format(bcolors.ENDC, result))

        def exit_handler():
            # save cli history
            save_history()
            # tell the thread to quit
            self.q.put('>>exit<<')
            # clear any colors
            print(bcolors.ENDC)

        atexit.register(exit_handler)
