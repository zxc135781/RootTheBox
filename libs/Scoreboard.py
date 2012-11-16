# -*- coding: utf-8 -*-

'''
Created on Oct 04, 2012

@author: moloch

    Copyright 2012 Root the Box

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''


import json
import threading

from uuid import uuid4
from models import Team
from datetime import datetime
from libs.GameHistory import GameHistory
from libs.SecurityDecorators import async


class Scoreboard(object):
    ''' Manages websocket connections (mostly thread safe) '''

    def __init__(self):
        self.history = GameHistory.Instance()

    def now(self):
        ''' Returns the current game state '''
        data = {}
        for team in Team.all():
            data[team.name] = {
                'money': team.money,
                'flags': [str(flag) for flag in team.flags],
                'game_levels': [str(lvl) for lvl in team.game_levels],
            }
        return json.dumps(data)