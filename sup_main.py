import flask, string, random, functools
import sup_user, sup_channels
import collections, re, os
from werkzeug.utils import secure_filename

app = flask.Flask(__name__)
app.secret_key = ''.join(random.choice(string.printable) for _ in range(20))
app.config['UPLOAD_FOLDER'] = '/Users/jamespetullo/sup/static'
def logged_in(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if 'logged_in' not in flask.session or not flask.session['logged_in']:
            return flask.redirect('/')
        return f(*args, **kwargs)
    return wrapper

def validate_user_chat(f):
    @functools.wraps(f)
    def wrapper(**kwargs):
        if not sup_channels.Channel.channel_exists(int(kwargs['channel_id'])):
            return flask.redirect('/dashboard')
        if 'logged_in' not in flask.session or not flask.session['logged_in'] or not sup_channels.Channel.belongs_to(flask.session['user_id'], kwargs['channel_id']):
            print('here', sup_channels.Channel.belongs_to(flask.session['user_id'], kwargs['channel_id']))
            return flask.redirect('/dashboard')
        return f(**kwargs)
    return wrapper

@app.route('/', methods=['GET'])
def home():
    return flask.render_template('sup_home.html')

@app.route('/login')
def login():
    _email = flask.request.args.get('email')
    _password = flask.request.args.get('password')
    _result = sup_user.User.login(_email, _password)
    if _result.succeeded == 'True':
        flask.session['user_id'] = _result.obj.id
        flask.session['logged_in'] = True
    return flask.jsonify({"succeeded":_result.succeeded, "message":_result.obj.message, 'target_class':_result.obj.target_class} if _result.succeeded == 'False' else {'succeeded':'True', 'id':_result.obj.id})

@app.route('/revert_to_gravatar', methods=['GET', 'POST'])
@logged_in
def revert_to_gravatar():
    sup_user.User.remove_old_avatar(flask.session['user_id'])
    return flask.redirect('/dashboard')

@app.route('/dashboard', methods=['GET', 'POST'])
@logged_in
def current_home():
    _user = sup_user.User.find_user(flask.session['user_id'])
    return flask.render_template('sup_user_home.html', user=_user.obj, current = _user.obj)

@app.route('/create-account')
def create_account():
    username = flask.request.args.get('username')
    email = flask.request.args.get('email')
    password = flask.request.args.get('password')
    _user = sup_user.User.create_user(username, email, password)
    if _user.succeeded == 'True':
        flask.session['user_id'] = _user.obj.id
        flask.session['logged_in'] = True
    return flask.jsonify({'succeeded':"False", 'target_class':_user.obj.target_class, 'message':_user.obj.message} if _user.succeeded == 'False' else {'succeeded':"True"})

@app.route('/user/<user_id>', methods=['GET'])
@logged_in
def user_home(user_id):
    _user = sup_user.User.find_user(user_id)
    if not _user.succeeded:
        return "<h1>user not found</h1>"
    if _user.obj.id == flask.session['user_id']:
        return flask.redirect('/dashboard')
    return flask.render_template('sup_user_home.html', user=_user.obj, current = sup_user.User.find_user(flask.session['user_id']).obj)

@app.route('/logout', methods=['GET'])
def logout():
    flask.session['logged_in'] = False
    return flask.redirect('/')

@app.route('/change-avatar', methods=['POST'])
def change_avatar():
    if 'file' not in flask.request.files:
        return flask.redirect('/dashboard')
    file = flask.request.files['file']
    if not file.filename:
        flask.redirect('/dashboard')
    print(file.filename, flask.session['user_id'])
    if file and re.findall('\.[a-z]+$', file.filename) and any(file.filename.endswith(i) for i in ['png', 'jpg']):
        print('got in here')
        sup_user.User.remove_old_avatar(flask.session['user_id'])
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f'{flask.session["user_id"]}_{filename}'))
    return flask.redirect('/dashboard')

@app.route('/change-cover-avatar', methods=['POST'])
def change_cover_avatar():

    if 'file' not in flask.request.files:
        return flask.redirect('/dashboard')
    file = flask.request.files['file']
    if not file.filename:
        flask.redirect('/dashboard')
    if file and re.findall('\.[a-z]+$', file.filename) and any(file.filename.endswith(i) for i in ['png', 'jpg']):
        sup_user.User.delete_cover_photo(flask.session['user_id'])
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f'{flask.session["user_id"]}cover_{filename}'))
    return flask.redirect('/dashboard')

@app.route('/delete_cover_photo', methods=['GET'])
@logged_in
def delete_cover_photo():
    sup_user.User.delete_cover_photo(flask.session['user_id'])
    return flask.redirect('/dashboard')


@app.route('/channel/<channel_id>', methods=['GET'])
@validate_user_chat
def channel_home(channel_id):
    return f'Soon the homepage of #{channel_id}'

@app.route('/create_channel')
def create_channel():
    _name = flask.request.args.get('name')
    if sup_channels.Channel.channel_name_exists(flask.session['user_id'], _name):
        return flask.jsonify({'status':'False'})
    _new_channel = sup_channels.Channel.create_channel(flask.session['user_id'], _name)
    return flask.jsonify({"status":"True", "channel_id":_new_channel.id})

@app.route('/update_profile_link')
def update_profile_link():
    sup_user.User.update_links(flask.session['user_id'], list(flask.request.args.items()))
    return flask.jsonify({'success':"true"})

@app.route('/chat_room_development', methods=['GET', 'POST'])
def channel_development():
    from hashlib import md5
    emails = [''.join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(4, 10)))+'@'+''.join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(4, 10)))+'.'+random.choice(['com', 'org', 'net']) for _ in range(16)]
    avatars = ['https://www.gravatar.com/avatar/{}?d=identicon'.format(md5(i.lower().encode('utf-8')).hexdigest()) for i in emails]
    avatar = collections.namedtuple('avatar', ['url', 'shade', 'id'])
    final_avatars = [avatars[i:i+4] for i in range(0, len(avatars), 4)]
    counter = iter(range(16))
    amount = iter(range(16))
    _t = [[avatar(b, next(counter) > 12, next(amount)) for b in i] for i in final_avatars]
    print(_t)
    return flask.render_template('chat_room.html', avatars = _t)

@app.errorhandler(404)
def page_not_found(e):
    return flask.render_template('404.html'), 404

if __name__ == '__main__':
    app.debug = True

app.run()
