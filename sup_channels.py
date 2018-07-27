import typing, collections, datetime
import re, random, tigerSqlite, string

class CreatedChannels:
    def __init__(self, _channels):
        self._channels = _channels
    def __bool__(self):
        return bool(self._channels)
    def __len__(self):
        return len(self._channels)
    def __repr__(self):
        return f'{self.__class__.__name__}({len(self._channels)} channel{"" if len(self._channels) == 1 else "s"})'
    def __iter__(self):
        for i in self._channels:
            yield i

class Channel:
    colors = ['IndianRed', 'LightCoral', 'Salmon', 'DarkSalmon', 'LightSalmon', 'Crimson', 'Red', 'FireBrick', 'DarkRed', 'Pink', 'LightPink', 'HotPink', 'DeepPink', 'MediumVioletRed', 'PaleVioletRed', 'LightSalmon', 'Coral', 'Tomato', 'OrangeRed', 'DarkOrange', 'Orange', 'Gold', 'Yellow', 'PapayaWhip', 'Moccasin', 'PaleGoldenrod', 'Khaki', 'DarkKhaki', 'Lavender', 'Thistle', 'Plum', 'Violet', 'Orchid', 'Fuchsia', 'Magenta', 'MediumOrchid', 'MediumPurple', 'RebeccaPurple', 'BlueViolet', 'DarkViolet', 'DarkOrchid', 'DarkMagenta', 'Purple', 'Indigo', 'SlateBlue', 'DarkSlateBlue', 'MediumSlateBlue', 'GreenYellow', 'Chartreuse', 'LawnGreen', 'Lime', 'LimeGreen', 'PaleGreen', 'LightGreen', 'MediumSpringGreen', 'SpringGreen', 'MediumSeaGreen', 'SeaGreen', 'ForestGreen', 'Green', 'DarkGreen', 'YellowGreen', 'OliveDrab', 'Olive', 'DarkOliveGreen', 'MediumAquamarine', 'DarkSeaGreen', 'LightSeaGreen', 'DarkCyan', 'Teal', 'Aqua', 'Cyan', 'LightCyan', 'PaleTurquoise', 'Aquamarine', 'Turquoise', 'MediumTurquoise', 'DarkTurquoise', 'CadetBlue', 'SteelBlue', 'LightSteelBlue', 'PowderBlue', 'LightBlue', 'SkyBlue', 'LightSkyBlue', 'DeepSkyBlue', 'DodgerBlue', 'CornflowerBlue', 'MediumSlateBlue', 'RoyalBlue', 'Blue', 'MediumBlue', 'DarkBlue', 'Navy', 'MidnightBlue', 'Cornsilk', 'BlanchedAlmond', 'Bisque', 'Wheat', 'BurlyWood', 'Tan', 'RosyBrown', 'SandyBrown', 'Goldenrod', 'DarkGoldenrod', 'Peru', 'Chocolate', 'SaddleBrown', 'Sienna', 'Brown', 'Maroon', 'HoneyDew', 'Azure', 'AliceBlue', 'SeaShell', 'Beige', 'OldLace', 'Linen', 'LavenderBlush', 'MistyRose', 'Gainsboro', 'Black']
    headers = ['id', 'createdon', 'about', 'owner', 'transcript', 'allowedusers', 'currentusers', 'topmessages', 'privatemessages', 'whiteboard', 'notepad']
    '''
    filename: channels.db
    tablename: channels
    rows:id int, createdon text, about:dict[name, description, rules, defaultroles, avatar, canpm] text, owner int, transcript:dict[poster_id, poster_username, date, message, tags] text, allowedusers:dict[userid, username, status, role, ismuted] text, currentusers:dict[id, username, avatar, role, canpm, ismuted] text,  topmessages:dict[starsnum, content] text, privatemessages:list[dict[id1, id2, transcript]] text, whiteboard text, notepad text
    raw_columns = 'id int, createdon text, about text, owner int, transcript text, allowedusers text, currentusers text, topmessages text, privatemessages text, whiteboard text, notepad text'
    '''
    def __init__(self, *_chat_data) -> None:
        self.__dict__ = dict(zip(self.__class__.headers, _chat_data))

    def __iter__(self):
        yield from [self.transcript[i:i+4] for i in range(0, len(self.transcript), 4)]

    @property
    def description(self) -> str:
        return ['', self.about['description']][bool(self.about['description'])]

    @property
    def rules(self):
        return ['', self.about['rules']][bool(self.about['rules'])]
    
    @property
    def has_avatar(self):
        return bool(self.about['avatar'])
    @property
    def channel_shield_color(self):
        return random.choice([self.__class__.colors[string.printable.index(i)] for i in self.channel_name])

    @property
    def channel_abbreviation(self):
        return self.channel_name[0]
        
    @property
    def avatar(self):
        return self.about['avatar']

    @property
    def href(self):
        return f'/channel/{self.id}'

    @property
    def manage_href(self):
        return f'/channel/manage/{self.id}'

    @property
    def length(self):
        return len(self.allowedusers)
    
    @property
    def channel_name(self) -> str:
        return self.about['name']

    @classmethod
    def create_channel(cls, _owner_id, _channel_name):
        _date = datetime.datetime.now()
        _current_channels = tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db').get_id('channels')
        _time = '{} {}'.format('-'.join(str(getattr(_date, i)) for i in ['month', 'day', 'year']), ':'.join(str(getattr(_date, i)) for i in ['hour', 'minute', 'second']))
        _row = [len(_current_channels)+1, _time, {'name':_channel_name, 'description':None, 'rules':None, 'avatar':None, 'default_role':'Standard user', 'can_pm':True}, _owner_id, [], [], [], [], [], '', '']
        _t = tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db')
        _t.insert('channels', *list(zip(cls.headers, _row)))
        return cls(*_row)
    @classmethod
    def channel_exists(cls, _id:int) -> bool:
        return any(int(i) == int(_id) for [i] in tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db').get_id('channels'))

    @classmethod
    def channels_owned(cls, _id:int) -> list:
        return CreatedChannels([cls(*i) for i in getattr(tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db'), f'get_{"_".join(cls.headers)}')('channels') if int(i[3]) == int(_id)])

    @classmethod
    def by_id(cls, _id:int):
        return cls(*[i for i in getattr(tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db'), f'get_{"_".join(cls.headers)}')('channels') if int(i[0]) == int(_id)][0])
    
    @classmethod
    def channels_joined(cls, _id:int) -> list:
        return CreatedChannels([cls(*i) for i in getattr(tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db'), f'get_{"_".join(cls.headers)}')('channels') if any(c['user_id'] == int(_id) for c in i[5])])

    @classmethod
    def channel_name_exists(cls, _id:int, _name:str) -> bool:
        return any(int(_owner) == int(_id) and _about['name'] == _name for _about, _owner in tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db').get_about_owner('channels'))

    @classmethod
    def belongs_to(cls, _user_id, _channel_id) -> bool:
        return any(((int(_owner) == int(_user_id) or any(int(c['user_id']) == int(_user_id) for c in _allowed_users))) and int(_id) == int(_channel_id) for _id,  _owner, _allowed_users in tigerSqlite.Sqlite('/Users/jamespetullo/sup/channels.db').get_id_owner_allowedusers('channels'))
       
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id={self.id}, name={self.about["name"]})'

if __name__ == '__main__':
    c = Channel.by_id(1)
    print(c.channel_shield_color)