from typing import Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from pexpect import spawn
import regex as re
import sys

class MsgType(Enum):
    CONSOLE = 0
    SCRIPT = 1
    CHAT = 2
    CONNECT = 3
    JOIN = 4
    SPECTATE = 5
    DISCONNECT = 6
    MAP_VOTE = 7
    MAP_CHANGE = 8
    MATCH_START = 9
    FRAG = 10
    SUICIDE = 11
    DUEL_WIN = 12

@dataclass
class OdasrvRegex:
    re_str: str
    msg_type: MsgType = MsgType.CONSOLE
    msg_subtype: str = ''

MAX_MSG_TYPE_NAME: int = max(len(t.name) for t in MsgType)

ODASRV_REGEXES: list[OdasrvRegex] = [
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] <CHAT> ((.+)+)', MsgType.CHAT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) has connected.', MsgType.CONNECT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) joined the game.', MsgType.JOIN),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) became a spectator.', MsgType.SPECTATE),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) disconnected\. .((.+)+)$', MsgType.DISCONNECT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) timed out\. .((.+)+)$', MsgType.DISCONNECT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) was kicked from the server!', MsgType.DISCONNECT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] Vote map ((.+)+) passed! .((.+)+)$', MsgType.MAP_VOTE),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] --- MAP(\d{2}): "(?P<map>(.+)+)" ---', MsgType.MAP_CHANGE),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] The match has started.', MsgType.MATCH_START),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was splintered by (?P<player>(.+)+)'s BFG.", MsgType.FRAG, 'bfg_direct'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) couldn't hide from (?P<player>(.+)+)'s BFG.", MsgType.FRAG, 'bfg_tracer'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) rode (?P<player>(.+)+)'s rocket.", MsgType.FRAG, 'rl'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) almost dodged (?P<player>(.+)+)'s rocket.", MsgType.FRAG, 'rl'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was splattered by (?P<player>(.+)+)'s super shotgun.", MsgType.FRAG, 'ssg'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was mowed down by (?P<player>(.+)+)'s chaingun.", MsgType.FRAG, 'cg'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) chewed on (?P<player>(.+)+)'s boomstick.", MsgType.FRAG, 'sg'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was melted by (?P<player>(.+)+)'s plasma gun.", MsgType.FRAG, 'plas'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was tickled by (?P<player>(.+)+)'s pea shooter.", MsgType.FRAG, 'pistol'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) chewed on (?P<player>(.+)+)'s fist.", MsgType.FRAG, 'fist'),
    OdasrvRegex(r"\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was mowed over by (?P<player>(.+)+)'s chainsaw.", MsgType.FRAG, 'saw'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<victim>(.+)+) was telefragged by (?P<player>(.+)+)\.', MsgType.FRAG, 'tele'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] Frag limit hit. Game won by (?P<player>(.+)+)!', MsgType.DUEL_WIN),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) should have stood back\.', MsgType.SUICIDE, 'rl'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) mutated\.', MsgType.SUICIDE, 'slime'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) cant swim\.', MsgType.SUICIDE, 'water'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) melted\.', MsgType.SUICIDE, 'lava'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) was squished\.', MsgType.SUICIDE, 'crusher'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) fell too far\.', MsgType.SUICIDE, 'falling'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) went boom\.', MsgType.SUICIDE, 'barrel'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) suicides\.', MsgType.SUICIDE, 'suicide'),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] (?P<player>(.+)+) tried to leave\.', MsgType.SUICIDE, 'exit'),
    OdasrvRegex(r'say ((.+)+)', MsgType.SCRIPT),
    OdasrvRegex(r'\[(\d{2}):(\d{2}):(\d{2})\] \[console\]: ((.+)+)', MsgType.SCRIPT)
]

class OdaSrvMsg:
    def __init__(self, line: str) -> None:
        self.line: str = line
        self.msg_date: datetime = datetime.now()
        self.odasrv_regex: OdasrvRegex = self.get_odasrv_regex()
        self.regex_match: re.Match[str] | None = re.match(self.odasrv_regex.re_str, line)
        self.msg_type: MsgType = self.odasrv_regex.msg_type
        self.player: str | None = self.regex_match['player'] if self.has_player_group() and self.regex_match else None
        self.map: str | None = self.regex_match['map'] if self.msg_type == MsgType.MAP_CHANGE and self.regex_match else None
        self.victim: str | None = self.regex_match['victim'] if self.msg_type == MsgType.FRAG  and self.regex_match else None
        self.weapon: str = self.odasrv_regex.msg_subtype

    def __str__(self) -> str:
        return f'> [{self.msg_type}] ' + (' ' * (MAX_MSG_TYPE_NAME - len(self.msg_type.name))) + self.line

    def get_odasrv_regex(self) -> OdasrvRegex:
        for reg in ODASRV_REGEXES:
            if re.match(reg.re_str, self.line):
                return reg
        return OdasrvRegex(r'\b\B') # will never match

    def has_player_group(self) -> bool:
        if self.msg_type in [MsgType.CONNECT, MsgType.JOIN, MsgType.SPECTATE, MsgType.DISCONNECT, MsgType.FRAG, MsgType.SUICIDE, MsgType.DUEL_WIN]:
            return True 
        return False    

class OdasrvInstance:
    def __init__(self, odasrv: Any) -> None:
        self.odasrv: Any = odasrv
        self.map_playing: str | None
        self.players_in_server: int = 0

    def read_stdout(self) -> None:
        line: str

        for line in iter(self.odasrv.readline, ''):
            msg: OdaSrvMsg = OdaSrvMsg(line)
            print(msg, end='')

            match msg.msg_type:
                case MsgType.CONSOLE:
                    continue
                case MsgType.CHAT:
                    _ = self.odasrv.sendline('say stop that chatter!')
                case MsgType.MAP_CHANGE:
                    self.map_playing = msg.map
                    _ = self.odasrv.sendline(f'say map is now {self.map_playing}')
                case MsgType.CONNECT:
                    self.players_in_server += 1
                    _ = self.odasrv.sendline(f'say there are {self.players_in_server} players in the server')
                case MsgType.DISCONNECT:
                    self.players_in_server -= 1
                    _ = self.odasrv.sendline(f'say {msg.player} went bye-bye, there are {self.players_in_server} players in the server now')
                case MsgType.FRAG:
                    _ = self.odasrv.sendline(f'say you already know but {msg.player} just fragged {msg.victim} with the {msg.weapon}')
                case MsgType.SUICIDE:
                    _ = self.odasrv.sendline('say ouch')
                case _: 
                    continue
                
def main() -> None:
    if len(sys.argv) != 2 or 'odasrv' not in sys.argv[1]:
        print(f"please supply your odasrv spawn command as one argument, ex: './odasrv -config path/to/my_cfg.cfg -waddir path/to/wads' ")
    else:
        odasrv: OdasrvInstance = OdasrvInstance(spawn(command=sys.argv[1], timeout=None, encoding='utf-8'))
        odasrv.read_stdout()


if __name__ == '__main__':
    main()
