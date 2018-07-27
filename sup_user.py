import re, datetime, collections
import typing, tigerSqlite, string, os
from hashlib import md5
import sup_channels

class Failed(typing.NamedTuple):
    target_class:str
    message:str

class Status(typing.NamedTuple):
    succeeded:str
    obj:list

class Social(typing.NamedTuple):
    icon:str
    name:str
    link:str

def login_validation(f):
    def wrapper(cls, email, password):
        #print(tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_email_password('users'))
        if not any(a == email and b == password for a, b in tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_email_password('users')):
            return Status("False", Failed('login_error_message', 'Invalid email and password combination'))
        return f(cls, email, password)
    return wrapper

def validate_user(f):
    def wrapper(cls, _id):
        if not any(int(i) == int(_id) for [i] in tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_id('users')):
            return Status(False, Failed(None, 'user id not found'))
        return f(cls, int(_id))
    return wrapper

def validate_parameters(f) -> typing.Callable:
    def wrapper(cls, _username, _email, _password):
        if cls.user_exists(username=_username, email = _email):
            return Status("False", Failed('new_name_issue', 'Username or password already exists'))
        if not re.findall('@|\.\w+$', _email):
            return Status("False", Failed('new_name_issue', 'Invalid email address'))
        if (len(_password) < 8) or (sum(i in _password for i in string.punctuation) == 0 or sum(i in _password for i in string.digits) == 0):
            return Status("False", Failed('new_password_issue', 'Passwords must be at least 8 characters long with at least 1 digit or special character'))
        return f(cls, _username, _email, _password)
    return wrapper

class User:
    headers = ['username', 'email', 'password', 'id', 'created', 'seen', 'links']
    '''
    filename: users.db
    tablename: users
    rows: username text, email text, password text, id int, created text, seen text, links text
    '''
    def __init__(self, _attr, _col = 'email') -> None:
        _user_data = getattr(tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db'), f'get_{"_".join(self.__class__.headers)}')('users')
        self.__dict__ = dict(zip(self.__class__.headers, [i for i in _user_data if dict(zip(self.__class__.headers, i))[_col] == _attr][0]))
        _avatar = [i for i in os.listdir('/Users/jamespetullo/sup/static') if i.startswith(str(self.id))]
        self.using_default_cover, self.cover_avatar= self.__class__.cover_photo(self.id)
        self.__dict__.update({'avatar':'https://www.gravatar.com/avatar/{}?d=identicon'.format(md5(self.email.lower().encode('utf-8')).hexdigest()), 'avatar_by_url':True} if not _avatar else {"avatar":_avatar[0], 'avatar_by_url':False})
        self.social = [Social(*i) for i in self.links]
        self.joined_channels = sup_channels.Channel.channels_joined(int(self.id))
        self.owned_channels = sup_channels.Channel.channels_owned(int(self.id))
    @property
    def has_social(self) -> bool:
        return bool(self.social)

    @classmethod
    def cover_photo(cls, _id) -> typing.Tuple[bool, str]:
        _option = [i for i in os.listdir('/Users/jamespetullo/sup/static') if i.startswith(f'{_id}cover')]
        return bool(_option), f'nature{int(_id)%6}.jpg' if not _option else _option[0]
    @classmethod
    def delete_cover_photo(cls, _id):
        _option = [i for i in os.listdir('/Users/jamespetullo/sup/static') if i.startswith(f'{_id}cover')]
        if _option:
            os.remove(f'/Users/jamespetullo/sup/static/{_option[0]}')

    @property
    def social_links(self) -> typing.List[typing.NamedTuple]:
        link = collections.namedtuple('link', ['name', 'icon', 'id'])
        _l = [['Youtube', "fab fa-youtube"], ['Google+', "fab fa-google-plus-g"], ['Linkedin', "fab fa-linkedin-in"], ['Facebook', "fab fa-facebook-square"], ['Personal Site', 'fas fa-link'], ['Github', "fab fa-github"], ['Twitter', "fab fa-twitter"]]
        return [link(*a, i) for i, a in enumerate(_l, 1)]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.id)

    @classmethod
    def user_exists(cls, **kwargs) -> bool:
        return any(any(b == kwargs.get(a) for a, b in zip(['username', 'email'], i)) for i in tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_username_password('users'))
    
    @classmethod
    def update_links(cls, _id:str, _raw_data:typing.List[typing.Tuple[str, str]]) -> None:
        link = collections.namedtuple('link', ['name', 'icon', 'id'])
        _l = [['Youtube', "fab fa-youtube"], ['Google+', "fab fa-google-plus-g"], ['Linkedin', "fab fa-linkedin-in"], ['Facebook', "fab fa-facebook-square"], ['Personal Site', 'fas fa-link'], ['Github', "fab fa-github"], ['Twitter', "fab fa-twitter"]]
        social_links = [link(*a, i) for i, a in enumerate(_l, 1)]
        _base = {i.id:i.name for i in social_links}
        _extra = {i.name:i.icon for i in social_links}
        _final_dict = {_base[int(re.findall('\d+', a)[0])]:b for a, b in _raw_data}
        current_links = [[Social(*i) for i in b] for a, b in tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_id_links('users') if int(a) == int(_id)][0]
        _converter = {i.name:i.link for i in current_links}
        _final_links = [[b, a, _final_dict[a] if a in _final_dict else _converter[a]] for a, b in _extra.items() if a in _converter or (a in _final_dict and _final_dict[a])]
        tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').update('users', [['links', _final_links]], [['id', _id]])
    @classmethod
    @login_validation
    def login(cls, _email, _password):
        return Status("True", cls(_email, _col='email'))

    @classmethod
    @validate_user
    def find_user(cls, _id):
        return Status(True, cls(_id, _col = 'id'))

    @classmethod
    @validate_parameters
    def create_user(cls, _username:str, _email:str, _password:str):
        _date = '-'.join(str(getattr(datetime.datetime.now(), i)) for i in ['month', 'day', 'year'])
        _time = ':'.join(str(getattr(datetime.datetime.now(), i)) for i in ['hour', 'minute', 'second'])
        _id = len(tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').get_id('users'))+1
        tigerSqlite.Sqlite('/Users/jamespetullo/sup/users.db').insert('users', *list(zip(cls.headers, [_username, _email, _password, _id, f'{_date} {_time}', f'{_date} {_time}', []])))
        return Status("True", cls(_id, _col = 'id')) 
    @classmethod
    def remove_old_avatar(cls, _id) -> None:
        _option = [i for i in os.listdir('/Users/jamespetullo/sup/static') if i.startswith(f'{_id}_')]
        if _option:
            print(_option)
            os.remove(f'/Users/jamespetullo/sup/static/{_option[0]}')
            
