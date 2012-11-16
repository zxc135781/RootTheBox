# -*- coding: utf-8 -*-
'''
Created on Mar 13, 2012

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
----------------------------------------------------------------------------

There's a lot of code in here ...

'''


from string import digits
from libs.Form import Form
from libs.SecurityDecorators import *
from models import dbsession, Team, Box, Flag, \
    Corporation, RegistrationToken, GameLevel, IpAddress
from handlers.BaseHandlers import BaseHandler


class AdminCreateHandler(BaseHandler):
    ''' Handler used to create game objects '''

    @authorized('admin')
    @restrict_ip_address
    def get(self, *args, **kwargs):
        ''' Renders Corp/Box/Flag create pages '''
        self.game_objects = {
            'corporation': 'admin/create/corporation.html',
            'box': 'admin/create/box.html',
            'flag': 'admin/create/flag.html',
            'team': 'admin/create/team.html',
            'game_level': 'admin/create/game_level.html'
        }
        if len(args) == 1 and args[0] in self.game_objects.keys():
            self.render(self.game_objects[args[0]], errors=None)
        else:
            self.render("public/404.html")

    @authorized('admin')
    @restrict_ip_address
    def post(self, *args, **kwargs):
        ''' Calls a function based on URL '''
        self.game_objects = {
            'corporation': self.create_corporation,
            'box': self.create_box,
            'flag': self.create_flag,
            'team': self.create_team,
            'game_level': self.create_game_level,
        }
        if len(args) == 1 and args[0] in self.game_objects.keys():
            self.game_objects[args[0]]()
        else:
            self.render("public/404.html")

    def create_corporation(self):
        ''' Add a new corporation to the database '''
        form = Form(
            corporation_name="Enter a corporation name",
            description="Please enter a description",
        )
        if form.validate(self.request.arguments):
            if Corporation.by_name(self.get_argument('corporation_name')) is not None:
                self.render("admin/create/corporation.html", errors=["Name already exists"])
            else:
                corporation = Corporation(
                    name=unicode(self.get_argument('corporation_name')),
                    description=unicode(self.get_argument('description')),
                )
                dbsession.add(corporation)
                dbsession.flush()
                self.redirect('/admin/view/game_objects')
        else:
            self.render("admin/create/corporation.html", errors=form.errors)

    def create_box(self):
        ''' Create a box object '''
        form = Form(
            box_name="Enter a box name",
            description="Enter a description",
            difficulty="Select a difficulty",
            corporation_uuid="Please select a corporation",
            game_level="Please select a game level",
        )
        if form.validate(self.request.arguments):
            try:
                if Box.by_name(self.get_argument('box_name')) is not None:
                    self.render("admin/create/box.html", errors=["Box name already exists"])
                elif Corporation.by_uuid(self.get_argument('corporation_uuid')) is None:
                    self.render("admin/create/box.html", errors=["Corporation does not exist"])
                elif GameLevel.by_number(int(self.get_argument('game_level'))) is None:
                    self.render("admin/create/box.html", errors=["Game level does not exist"])
                else:
                    self.__mkbox__()
                    self.redirect('/admin/view/game_objects')
            except ValueError:
                self.render('admin/view/create.html', errors=["Invalid level number"])
        else:
            self.render("admin/create/box.html", errors=form.errors)

    def create_flag(self):
        ''' Create a flag '''
        form = Form(
            box_uuid="Please select a box",
            flag_name="Please enter a name",
            token="Please enter a token value",
            reward="Please enter a reward value",
            is_file="Please select a file setting",
            description="Please enter a flag description",
        )
        if form.validate(self.request.arguments):
            try:
                if Flag.by_name(self.get_argument('flag_name')) is not None:
                    self.render('admin/create/flag.html', errors=["Name already exists"])
                elif Flag.by_token(self.get_argument('token')) is not None:
                    self.render('admin/create/flag.html', errors=["Token value is not unique"])
                elif Box.by_uuid(self.get_argument('box_uuid')) is None:
                    self.render('admin/create/flag.html', errors=["Box does not exist"])
                else:
                    reward = int(self.get_argument('reward', 'NaN'))
                    self.__mkflag__(reward)
                    self.redirect('/admin/view/game_objects')
            except ValueError:
                self.render('admin/create/flag.html', errors=["Invalid reward value"])
        else:
            self.render("admin/create/flag.html", errors=form.errors)

    def create_team(self):
        ''' Create a new team in the database '''
        form = Form(team_name="Enter a team name", motto="Enter a team motto")
        if form.validate(self.request.arguments):
            team = Team(
                name=unicode(self.get_argument('team_name')),
                motto=unicode(self.get_argument('motto')),
            )
            dbsession.add(team)
            dbsession.flush()
            self.redirect('/admin/view/user_objects')
        else:
            self.render("admin/create/team.html", errors=form.errors)

    def create_game_level(self):
        ''' Creates a game level '''
        form = Form(
            level_number="Please enter a level number",
            buyout="Please enter a buyout value",
        )
        if form.validate(self.request.arguments):
            try:
                game_level = int(self.get_argument('level_number'))
                buyout = int(self.get_argument('buyout'))
                if game_level <= 0:
                    self.render('admin/create/game_level.html', errors=["Level number must be greater than 0"])
                elif GameLevel.by_number(game_level) is not None:
                    self.render('admin/create/game_level.html', errors=["Game level number must be unique"])
                elif buyout < 0:
                    self.render('admin/create/game_level.html', errors=["Buyout value must be greater than or equal to 0"])
                else:
                    self.__mklevel__(game_level, buyout)
                    self.redirect('/admin/view/game_levels')
            except ValueError:
                self.render('admin/create/game_level.html', errors=["Invalid level number"])
        else:
            self.render('admin/create/game_level.html', errors=form.errors)

    def __mkbox__(self):
        ''' Creates a box in the database '''
        corp = Corporation.by_uuid(self.get_argument('corporation_uuid'))
        level = GameLevel.by_number(int(self.get_argument('game_level')))
        box = Box(
            name=unicode(self.get_argument('box_name')),
            description=unicode(self.get_argument('description')),
            difficulty=unicode(self.get_argument('difficulty')),
            corporation_id=corp.id,
            game_level_id=level.id,
        )
        dbsession.add(box)
        dbsession.flush()

    def __mklevel__(self, game_level, buyout):
        ''' 
        Creates a new level in the database, the levels are basically a linked-list
        where each level points to the next, and the last points to None.  This 
        function creates a new level and sorts everything based on the 'number' attrib
        '''
        new_level = GameLevel(
            number=game_level,
            buyout=buyout,
        )
        game_levels = GameLevel.all()
        game_levels.append(new_level)
        game_levels = sorted(game_levels)
        index = 0
        for level in game_levels[:-1]:
            level.next_level_id = game_levels[index + 1].id
            dbsession.add(level)
            index += 1
        game_levels[0].number = 0
        dbsession.add(game_levels[0])
        game_levels[-1].next_level_id = None
        dbsession.add(game_levels[-1])
        dbsession.flush()

    def __mkflag__(self, reward):
        ''' Creates a flag in the database '''
        box = Box.by_uuid(self.get_argument('box_uuid'))
        flag = Flag(
            name=unicode(self.get_argument('flag_name')),
            token=unicode(self.get_argument('token')),
            description=unicode(self.get_argument('description')),
            is_file=bool(self.get_argument('is_file', 'false') == 'true'),
            box_id=box.id,
            value=reward,
        )
        dbsession.add(flag)
        dbsession.flush()


class AdminViewHandler(BaseHandler):
    ''' View game objects '''

    @authorized('admin')
    @restrict_ip_address
    def get(self, *args, **kwargs):
        ''' Calls a view function based on URI '''
        uri = {
            'game_objects': self.view_game_objects,
            'game_levels': self.view_game_levels,
            'user_objects': self.view_user_objects,
        }
        if len(args) == 1 and args[0] in uri.keys():
            uri[args[0]]()
        else:
            self.render("public/404.html")

    def view_game_objects(self):
        ''' Renders the view corporations page '''
        self.render("admin/view/game_objects.html", errors=None)

    def view_game_levels(self):
        self.render("admin/view/game_levels.html", errors=None)

    def view_user_objects(self):
        ''' Renders the view registration token page '''
        self.render('admin/view/user_objects.html', errors=None)


class AdminAjaxObjectDataHandler(BaseHandler):
    ''' Handles AJAX data for admin handlers '''

    @authorized('admin')
    @restrict_ip_address
    def get(self, *args, **kwargs):
        game_objects = {
            'game_level': GameLevel,
            'corporation': Corporation,
            'flag': Flag,
            'user': User,
            'team': Team,
            'box': Box,
        }
        obj_name = self.get_argument('obj', '')
        uuid = self.get_argument('uuid', '')
        if obj_name in game_objects.keys():
            obj = game_objects[obj_name].by_uuid(uuid)
            if obj is not None:
                self.write(obj.to_dict())
            else:
                self.write({'Error':'Invalid uuid.'})
        else:
            self.write({'Error':'Invalid object type.'})
        self.finish()


class AdminEditHandler(BaseHandler):
    ''' Edit game objects '''

    @authorized('admin')
    @restrict_ip_address
    def post(self, *args, **kwargs):
        ''' Calls an edit function based on URL '''
        uri = {
            'corporation': self.edit_corporations,
            'box': self.edit_boxes,
            'flag': self.edit_flags,
            'team': self.edit_teams,
            'user': self.edit_users,
            'ipv4': self.edit_ipv4,
            'ipv6': self.edit_ipv6,
            'game_level': self.edit_game_level,
            'box_level': self.box_level,
        }
        if len(args) == 1 and args[0] in uri.keys():
            uri[args[0]]()
        else:
            self.render("public/404.html")

    def edit_corporations(self):
        ''' Updates corporation object in the database '''
        form = Form(
            uuid="Object not selected",
            name="Missing corporation name",
            description="Missing description",
        )
        if form.validate(self.request.arguments):
            corp = Corporation.by_uuid(self.get_argument('uuid'))
            if corp is not None:
                if self.get_argument('name') != corp.name:
                    logging.info("Updated corporation name %s -> %s" % (corp.name, self.get_argument('name'),))
                    corp.name = unicode(self.get_argument('name'))
                if self.get_argument('description') != corp.description:
                    logging.info("Updated corporation description %s -> %s" % (corp.description, self.get_argument('description'),))
                    corp.description = unicode(self.get_argument('description'))
                dbsession.add(corp)
                dbsession.flush()
                self.redirect('/admin/view/game_objects')
            else:
                self.render("admin/view/game_objects.html", errors=["Corporation does not exist"])
        else:
            self.render("admin/view/game_objects.html", errors=form.errors)

    def edit_boxes(self):
        ''' Edit existing boxes in the database '''
        form = Form(
            uuid="Object not selected",
            name="Missing box name",
            corporation_uuid="Please select a corporation",
            description="Please enter a description",
            difficulty="Please enter a difficulty",
        )
        if form.validate(self.request.arguments):
            box = Box.by_uuid(self.get_argument('uuid'))
            if box is not None:
                errors = []
                if self.get_argument('name') != box.name:
                    if Box.by_name(self.get_argument('name')) is None:
                        logging.info("Updated box name %s -> %s" % (box.name, self.get_argument('name'),))
                        box.name = unicode(self.get_argument('name'))
                    else:
                        errors.append("Box name already exists")
                corp = Corporation.by_uuid(self.get_argument('corporation_uuid'))
                if corp is not None and corp.id != box.corporation_id:
                    logging.info("Updated %s's corporation %s -> %s" % (box.name, box.corporation_id, corp.id,))
                    box.corporation_id = corp.id
                elif corp is None:
                    errors.append("Corporation does not exist")
                if self.get_argument('description') != box.description:
                    logging.info("Updated %s's description %s -> %s" % (box.name, box.description, self.get_argument('description'),))
                    box.description = unicode(self.get_argument('description'))
                if self.get_argument('difficulty') != box.difficulty:
                    logging.info("Updated %s's difficulty %s -> %s" % (box.name, box.difficulty, self.get_argument('difficulty'),))
                    box.difficulty = unicode(self.get_argument('difficulty'))
                dbsession.add(box)
                dbsession.flush()
                self.render("admin/view/game_objects.html", errors=errors)
            else:
                self.render("admin/view/game_objects.html", errors=["Box does not exist"])
        else:
            self.render("admin/view/game_objects.html", errors=form.errors)

    def edit_flags(self):
        ''' Super ugly code, yes - Edit existing flags in the database '''
        form = Form(
            uuid="Object not selected",
            name="Please enter a name",
            token="Please enter a toke value",
            description="Please provide a description",
            value="Please enter a reward value",
            box_uuid="Please select a box",
        )
        if form.validate(self.request.arguments):
            flag = Flag.by_uuid(self.get_argument('uuid'))
            if flag is not None:
                errors = []
                if flag.name != self.get_argument('name'):
                    if Flag.by_name(unicode(self.get_argument('name'))) is None:
                        logging.info("Updated flag name %s -> %s" % (flag.name, self.get_argument('name'),))
                        flag.name = unicode(self.get_argument('name'))
                    else:
                        errors.append("Flag name already exists")
                if flag.token != self.get_argument('token'):
                    if Flag.by_token(unicode(self.get_argument('token'))) is None:
                        logging.info("Updated %s's token %s -> %s" % (flag.name, flag.token, self.get_argument('token'),))
                        flag.token = unicode(self.get_argument('token'))
                    else:
                        errors.append("Token is not unique")
                if flag.description != self.get_argument('description'):
                    logging.info("Updated %s's description %s -> %s" % (flag.name, flag.description, self.get_argument('description'),))
                    flag.description = unicode(self.get_argument('description'))
                try:
                    reward_value = int(self.get_argument('value'))
                    if reward_value != flag.value:
                        logging.info("Updated %s's value %d -> %d" % (flag.name, flag.value, reward_value,))
                        flag.value = reward_value
                except ValueError:
                    errors.append("Invalid reward amount")
                box = Box.by_uuid(self.get_argument('box_uuid'))
                if box is not None and box.id != flag.box_id:
                    logging.info("Updated %s's box %d -> %d" % (flag.name, flag.box_id, box.id))
                    flag.box_id = box.id
                elif box is None:
                    errors.append("Box does not exist")
                dbsession.add(flag)
                dbsession.flush()
                self.render("admin/view/game_objects.html", errors=errors)
            else:
                self.render("admin/view/game_objects.html", errors=["Flag does not exist"])
        else:
            self.render("admin/view/game_objects.html", errors=form.errors)

    def edit_teams(self):
        ''' Edit existing team objects in the database '''
        form = Form(
            uuid="No team selected",
            name="Please enter a name",
            motto="Please enter a motto",
            listen_port="Please enter a listen port",
        )
        if form.validate(self.request.arguments):
            team = Team.by_uuid(self.get_argument('uuid'))
            if team is not None:
                errors = []
                if team.name != self.get_argument('name'):
                    logging.info("Updated team name %s -> %s" % (team.name, self.get_argument('name'),))
                    team.name = unicode(self.get_argument('name'))
                if team.motto != self.get_argument('motto'):
                    logging.info("Updated %s's motto %s -> %s" % (team.name, team.motto, self.get_argument('motto'),))
                    team.motto = unicode(self.get_argument('motto'))
                try:
                    lport = int(self.get_argument('listen_port'))
                    if lport != team.listen_port:
                        logging.info("Updated %s's listen port %d -> %d" % (team.name, team.listen_port, lport,))
                        team.listen_port = lport
                except ValueError:
                    errors.append("Invalid listen port %s " % self.get_argument('listen_port'))
                dbsession.add(team)
                dbsession.flush()
                self.redirect("/admin/view/user_objects")
            else:
                self.render("admin/view/user_objects.html", errors=["Team does not exist"])
        else:
            self.render("admin/view/user_objects.html", errors=form.errors)

    def edit_users(self):
        ''' Update user objects in the database '''
        form = Form(
            uuid="User not selected",
            account="Please enter an account name",
            handle="Please enter a handle name",
            hash_algorithm="Please select a hash algorithm",
            team_uuid="Please select a team",
        )
        if form.validate(self.request.arguments):
            errors = []
            user = User.by_uuid(self.get_argument('uuid'))
            if user is not None:
                # Update user account name
                if user.account != self.get_argument('account'):
                    if User.by_account(self.get_argument('account')) is None:
                        logging.info("Updated user account %s -> %s" % (user.account, self.get_argument('account'),))
                        user.account = unicode(self.get_argument('account'))
                    else:
                        errors.append("Account name is already in use")
                # Update user handle
                if user.handle != self.get_argument('handle'):
                    if User.by_handle(self.get_argument('handle')) is None:
                        logging.info("Updated user handle %s -> %s" % (user.handle, self.get_argument('handle'),))
                        user.handle = unicode(self.get_argument('handle'))
                    else:
                        errors.append("Handle is already in use")
                # Update hashing algoritm
                if self.get_argument('hash_algorithm') in user.algorithms.keys():
                    if user.algorithm != self.get_argument('hash_algorithm'):
                        if 0 < len(self.get_argument('password', '')):
                            logging.info("Updated %s's hashing algorithm %s -> %s" % (user.handle, user.algorithm, self.get_argument('hash_algorithm')))
                            user.algorithm = self.get_argument('hash_algorithm')
                        else:
                            errors.append("You must provide a password when updating the hashing algorithm")
                else:
                    errors.append("Not a valid hash algorithm")
                # Update password
                if 0 < len(self.get_argument('password', '')):
                    user.password = self.get_argument('password')
                # Update team
                team = Team.by_uuid(self.get_argument('team_uuid'))
                if team is not None:
                    if user.team_id != team.id:
                        logging.info("Updated %s's team %s -> %s" % (user.handle, user.team_id, team.name))
                        user.team_id = team.id
                else:
                    errors.append("Team does not exist in database")
                dbsession.add(user)
                dbsession.flush()
            else:
                errors.append("User does not exist")
            self.render("admin/view/user_objects.html", errors=errors)
        else:
            self.render("admin/view/user_objects.html", errors=form.errors)

    def edit_ipv4(self):
        ''' Add ipv4 addresses to a box (sorta edits the box object) '''
        form = Form(box_uuid="Select a box", ipv4="Please provide a list of IPv4 addresses")
        if form.validate(self.request.arguments):
            errors = []
            box = Box.by_uuid(self.get_argument('box_uuid'))
            if box is not None:
                ips_string = self.get_argument('ipv4').replace('\n', ',')
                ips = filter(lambda char: char in "1234567890.,", ips_string).split(",")
                for ip in filter(lambda ip: 0 < len(ip), ips):
                    try:
                        if Box.by_ip_address(ip) is None:
                            addr = IpAddress(box_id=box.id, v4=ip)
                            dbsession.add(addr)
                        else:
                            errors.append("%s has already been assigned to %s." % (ip, box.name,))
                    except ValueError:
                        errors.append("'%s' is not a valid IPv4 address" % str(ip[:15]))
                dbsession.flush()
            else:
                errors.append("Box does not exist")
            self.render("admin/view/game_objects.html", errors=errors)
        else:
            self.render("admin/view/game_objects.html", errors=form.errors)

    def edit_ipv6(self):
        ''' Add ipv6 addresses to a box (sorta edits the box object) '''
        form = Form(box_uuid="Select a box", ipv6="Please provide a list of IPv6 addresses")
        if form.validate(self.request.arguments):
            errors = []
            box = Box.by_uuid(self.get_argument('box_uuid'))
            if box is not None:
                ips_string = self.get_argument('ipv6').replace('\n', ',').lower()
                ips = filter(lambda char: char in "1234567890abcdef:,", ips_string).split(",")
                for ip in filter(lambda ip: 0 < len(ip), ips):
                    try:
                        box = Box.by_ip_address(ip)
                        if box is None:
                            addr = IpAddress(box_id=box.id, v6=ip)
                            dbsession.add(addr)
                        else:
                            errors.append("%s has already been assigned to %s." % (ip, box.name,))
                    except ValueError:
                        errors.append("'%s' is not a valid IPv6 address" % str(ip[:39]))
                dbsession.flush()
            else:
                errors.append("Box does not exist")
            self.render("admin/view/game_objects.html", errors=errors)
        else:
            self.render("admin/view/game_objects.html", errors=form.errors)

    def edit_game_level(self):
        ''' Update game level objects '''
        form = Form(uuid="Select an object", number="Enter a level number", buyout="Enter a buyout value")
        if form.validate(self.request.arguments):
            errors = []
            level = GameLevel.by_uuid(self.get_argument('uuid'))
            try:
                new_number = int(self.get_argument('number', 'NaN'))
                new_buyout = int(self.get_argument('buyout', 'NaN'))
                if level.number != new_number and GameLevel.by_number(new_number) is None:
                    level.number = new_number
                    dbsession.add(level)
                    dbsession.flush()
                    # Fix the linked-list
                    game_levels = sorted(GameLevel.all())
                    index = 0
                    for game_level in game_levels[:-1]:
                        game_level.next_level_id = game_levels[index + 1].id
                        dbsession.add(game_level)
                        index += 1
                    game_levels[0].number = 0
                    dbsession.add(game_levels[0])
                    game_levels[-1].next_level_id = None
                    dbsession.add(game_levels[-1])
                    dbsession.flush()
                if GameLevel.by_number(new_number) is not None:
                    errors.append("GameLevel number is not unique")
                if level.buyout != new_buyout:
                    level.buyout = new_buyout
                    dbsession.add(level)
                    dbsession.flush()                    
            except ValueError:
                errors.append("That was not a number ... maybe you should go back to school")
            self.render("admin/view/game_levels.html", errors=errors)
        else:
            self.render("admin/view/game_levels.html", errors=form.errors)

    def box_level(self):
        ''' Changes a boxs level '''
        form = Form(box_uuid="No box selected", level_uuid="No level selected")
        if form.validate(self.request.arguments):
            errors = []
            box = Box.by_uuid(self.get_argument('box_uuid'))
            level = GameLevel.by_uuid(self.get_argument('level_uuid'))
            if box is not None and level is not None:
                box.game_level_id = level.id
                dbsession.add(box)
                dbsession.flush()
            elif box is None:
                errors.append("Box does not exist")
            elif level is None:
                errors.append("GameLevel does not exist")
            self.render("admin/view/game_levels.html", errors=errors)
        else:
            self.render("admin/view/game_levels.html", errors=form.errors)

class AdminDeleteHandler(BaseHandler):
    ''' Manages registration tokens '''

    @authorized('admin')
    @restrict_ip_address
    def post(self, *args, **kwargs):
        ''' Used to delete database objects '''
        uri = {
            'ip': self.del_ip,
            'flag': self.del_flag,
        }
        if len(args) == 1 and args[0] in uri.keys():
            uri[args[0]]()
        else:
            self.render("public/404.html")

    def del_ip(self):
        ''' Delete an ip address object '''
        ip = IpAddress.by_address(self.get_argument('ip', '__NULL__'))
        if ip is not None:
            logging.info("Deleted IP address: '%s'" % str(ip))
            dbsession.delete(ip)
            dbsession.flush()
            self.redirect("/admin/view/game_objects")
        else:
            logging.info("IP address (%s) does not exist in database" % self.get_argument('ip', '__NULL__'))
            self.render("admin/view/game_objects.html", errors=["IP does not exist in database"])

    def del_flag(self):
        ''' Delete a flag object from the database '''
        flag = Flag.by_uuid(self.get_argument('uuid', '__NULL__'))
        if flag is not None:
            logging.info("Deleted flag: %s " % flag.name)
            dbsession.delete(flag)
            dbsession.flush()
            self.redirect('/admin/view/game_objects')
        else:
            logging.info("Flag (%s) does not exist in the database" % self.get_argument('uuid', '__NULL__'))
            self.render("admin/view/game_objects.html", errors=["Flag does not exist in database"])


class AdminRegTokenHandler(BaseHandler):
    ''' Manages registration tokens '''

    @authorized('admin')
    @restrict_ip_address
    def get(self, *args, **kwargs):
        uri = {
            'create': self.create,
            'view': self.view,
        }
        if len(args) == 1 and args[0] in uri.keys():
            uri[args[0]]()
        else:
            self.render("public/404.html")

    @authorized('admin')
    @restrict_ip_address
    def post(self, *args, **kwargs):
        ''' Used to delete regtokens '''
        token_value = self.get_argument('token_value', '__NULL__')
        reg_token = RegistrationToken.by_value(token_value)
        if reg_token is not None:
            dbsession.delete(reg_token)
            dbsession.flush()
            self.redirect('/admin/regtoken/view')
        else:
            self.render('admin/view/token.html', errors=["Token does not exist"])

    def create(self):
        ''' Adds a registration token to the db and displays the value '''
        token = RegistrationToken()
        dbsession.add(token)
        dbsession.flush()
        self.render('admin/create/token.html', token=token)
    
    def view(self):
        ''' View all reg tokens '''
        self.render('admin/view/token.html', errors=None)
