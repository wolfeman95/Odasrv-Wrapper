from pexpect import spawn
import regex as re
import dateutil.parser


class BaseMessage:
    '''datetime of message, publish message method'''

    def __init__(self, line):
        self.line = line

        # make sure to set log_fulltimestamps "1" in your odasrv.cfg
        self.date_time = str(dateutil.parser.parse(" ".join(line.split()[0:2])[1:-1], dayfirst=True))

    def publish_message(self):
        print(f'got line: {self.line}')

    def publish_date(self):
        print(f'datetime: {self.date_time}')

class PlayerChatMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). <CHAT> ((.+)+)']

class PlayerConnectMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) has connected.']

class PlayerDisconnectMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) disconnected\. .((.+)+)$',
                r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) timed out\. .((.+)+)$']

class PlayerJoinMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) joined the game.']

class PlayerSpectateMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) became a spectator.']

class MapVoteMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). Vote map ((.+)+) passed! .((.+)+)$']

class MapChangeMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). --- MAP(\d{2}): "(?P<map>(.+)+)" ---']

class PlayerCapMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) has captured the (?P<flag>(.+)) flag .held for (?P<odatime>(\d):(\d{2}).(\d{2})).']

class PlayerPickupMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) picked up the (?P<flag>(.+)) flag']


def stdout_reader(odasrv):
    """
    Analyzing the odasrv stdout and sending messages to the server
    """

    map_playing = ""
    players_in_server = 0


    for line in iter(odasrv.readline, b''):
        print(f'got line: {line}')

        # chat
        if re.match(PlayerChatMessage.PATTERNS[0], line):
            odasrv.sendline('say stop that chatter!')

        # map change
        if re.match(MapChangeMessage.PATTERNS[0], line):
            map_playing = re.match(MapChangeMessage.PATTERNS[0], line).group('map')
            odasrv.sendline(f'say map is now {map_playing}')

        # player connect
        if any(re.match(pattern, line) for pattern in PlayerConnectMessage.PATTERNS):
            players_in_server += 1
            odasrv.sendline(f'say there are {str(players_in_server)} players in the server')

        # player disconnect / timeout
        if any(re.match(pattern, line) for pattern in PlayerDisconnectMessage.PATTERNS):
            players_in_server -= 1
            odasrv.sendline(f'say there are {str(players_in_server)} players in the server')



def main():

    odasrv = spawn('./odasrv -config ./odasrv.cfg', timeout=None, encoding='utf-8')

    stdout_reader(odasrv)


if __name__ == '__main__':
    main()
