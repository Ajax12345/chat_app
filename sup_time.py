import datetime, typing
import re
def format_input(f):
    def wrapper(cls, _data):
        if isinstance(_data, list) and any(not isinstance(i, int) for i in _data):
            raise TypeError('Input must be all integer values')
        return f(cls, _data if isinstance(_data, list) else list(map(int, re.findall('\d+', _data))))
    return wrapper

def validate_setitem(f):
    def wrapper(cls, _name, _var):
        if _name not in ['abbrev']:
            raise AttributeError(f"Cannot bind '{_name}' to {cls.__class__.__name__}")
        return f(cls, _name, _var)
    return wrapper

_SupTime = typing.TypeVar('SupTime')

class SupTime:
    time_headers = ['year', 'month', 'day', 'hour', 'minute', 'second']
    @format_input
    def __init__(self, _time:typing.List[int]) -> None:
        self.__dict__ = dict(zip(self.__class__.time_headers, _time))
    
    @validate_setitem
    def __setitem__(self, _attr, _val):
        setattr(self, _attr, _val)

    @property
    def full_date(self):
        _months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        return '{} {} {}, at {}:{}'.format(_months[self.month-1] if not getattr(self, 'abbrev', False) else _months[self.month-1][:3], self.day, self.year, self.hour, self.second)

    @classmethod
    def current_time(cls):
        return cls([getattr(datetime.datetime.now(), i) for i in cls.time_headers])

    @property
    def to_List(self):
        return [getattr(self, i) for i in self.__class__.time_headers]
    def __sub__(self, _time_obj:typing.Type[_SupTime]) -> str:
        '''oldest time must be subtracted from newest time'''
        _start = self.to_List
        _end = _time_obj.to_List
        converter = {0:lambda _:12, 1:lambda x:30 if x in [4, 6, 11, 9] else 31, 2:lambda _:24, 3:lambda _:60, 4:lambda _:60, 5:lambda _: None}
        difference = [i for i in range(len(_start)+1) if all(a == b for a, b in zip(_start[:i+1], _end[:i+1]))]
        
        if len(difference) == 7:
            return 'Just now'
        if len(difference) == 5:
            return '{} second{} ago'.format(abs(_start[-1]-_end[-1]), ['s', ''][abs(_start[-1]-_end[-1]) == 1])
        if not difference:
            difference = [-1]
        t1, t2 = _start[difference[-1]+1], _end[difference[-1]+1]
        trailing1, trailing2 = _start[difference[-1]+2], _end[difference[-1]+2]
        if trailing1 > trailing2:
            return '{} {}{} ago'.format(t1-t2, self.__class__.time_headers[difference[-1]+1], ['s', ''][t1-t2 == 1])
        
        _diff = converter[difference[-1]+1](t1)-trailing2
        t2 += 1
        if not (t1 - t2):
            if (trailing1+_diff)//converter[difference[-1]+2]:
                return '{} {}{} ago'.format((trailing1+_diff)//converter[difference[-1]+2], self.__class__.time_headers[difference[-1]+1], ['s', ''][(trailing1+_diff)//converter[difference[-1]+1]])
            return '{} {}{} ago'.format(trailing1+_diff, self.__class__.time_headers[difference[-1]+2], ['s', ''][trailing1+_diff == 1])

        return '{} {}{} ago'.format(t1-t2, self.__class__.time_headers[difference[-1]+1], ['s', ''][t1-t2 == 1])

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, ', '.join(f'{i}={getattr(self, i)}' for i in self.__class__.time_headers))