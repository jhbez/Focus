# -*- coding: utf-8 -*-
# ZERO 1/0 © 2016
from flask import Flask, request, render_template, send_from_directory, g, session, url_for, redirect
from AoL.Utils.Db import PsqlAoL
from flask_restful import Api
from AoL.Auth.Auth import Auth
from AoL.Auth.User import UserList
from AoL.Habit.Habit import Habit, HabitList
from AoL.Habit.HabitHistory import HistoryHabit, HistoryHabitList
from AoL.Project.Project import Project, ProjectList
from AoL.Project.ProjectTask import ProjectTask, ProjectTaskList
from AoL.Project.ProjectTaskParticipated import ProjectParticipated, ProjectParticipatedList
from AoL.Project.ProjectTaskIssue import ProjectIssue, ProjectIssueList
from AoL.Wish.Wish import Wish, WishList
from AoL.Dream.Dream import Dream, DreamList
from AoL.Pending.Pending import Pending, PendingList
# UL
from UL.Dashboard.Dashboard import DashboardCtl
from UL.Project.Project import ProjectCtl
from UL.Yourself.Yourself import YourselfCtl
app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')
api = Api(app)


@app.before_request
def open_db():
    g.db_conn = PsqlAoL(
        user=app.config.get('DB_USER'),
        password=app.config.get('DB_PASSWORD'),
        database=app.config.get('DB_NAME'),
        port=app.config.get('DB_PORT'),
        host=app.config.get('DB_HOST')
    )
    if g.db_conn:
        g.db_conn.execute("set timezone to 'UTC';")
    _url_path = str(request.url_rule)
    _url_endpoint = str(request.endpoint)
    _url = _url_path.replace(_url_endpoint, '')
    if api_v1 in _url:
        if _url_endpoint != 'login':
            _token = request.headers.get('X-Authorization')
            # print session
            if 'X-Authorization' in session and 'user' in session:
                _token = session['X-Authorization']
            _auth = Auth()
            _rs = _auth.is_login(token=_token)
            if 'error' in _rs:
                return _rs['error']
            else:
                g.user = _rs['user']

# RESTful AOL
api_v1 = '/api/v1/'
# Habit
api.add_resource(HabitList, api_v1 + 'habit')
api.add_resource(Habit, api_v1 + 'habit/<int:habit_id>')
api.add_resource(HistoryHabitList, api_v1 + 'habit/history')
api.add_resource(HistoryHabit, api_v1 + 'habit/history/<int:history_habit_id>')
# Project
api.add_resource(ProjectList, api_v1 + 'project')
api.add_resource(Project, api_v1 + 'project/<int:id>')
api.add_resource(ProjectTaskList, api_v1 + 'project/task')
api.add_resource(ProjectTask, api_v1 + 'project/task/<int:id>')
api.add_resource(ProjectParticipatedList, api_v1 + 'project/task/participated')
api.add_resource(ProjectParticipated, api_v1 + 'project/task/participated/<int:id>')
api.add_resource(ProjectIssueList, api_v1 + 'project/task/issue')
api.add_resource(ProjectIssue, api_v1 + 'project/task/issue/<int:id>')
# wish
api.add_resource(WishList, api_v1 + 'wish')
api.add_resource(Wish, api_v1 + 'wish/<int:id>')
# dream
api.add_resource(DreamList, api_v1 + 'dream')
api.add_resource(Dream, api_v1 + 'dream/<int:id>')
# Pending
api.add_resource(PendingList, api_v1 + 'pending')
api.add_resource(Pending, api_v1 + 'pending/<int:id>')
# User
api.add_resource(UserList, api_v1+'user')


@app.route(api_v1 + 'login', methods=['POST'])
def login():
    _data = request.json
    _auth = Auth()
    return _auth.login(data=_data)


# Web App
@app.route('/', endpoint='/')
def index():
    return render_template('index.html')


@app.route('/<path:resource>')
def serveStaticResource(resource):
    return send_from_directory('static/', resource)


prefix_admin = app.config.get('PREFIX_ADMIN')
startpoint_admin = prefix_admin[1:]


@app.context_processor
def prefix_admin_template():
    return dict(prefix_admin=startpoint_admin)


def is_login(func):
    def func_wrapper():
        if 'X-Authorization' not in session and 'user' not in session:
            return redirect(url_for('/'))
        else:
            return func()
    return func_wrapper


@app.route('/logout', endpoint='/logout')
@is_login
def logout():
    session.pop('X-Authorization', None)
    session.pop('user', None)
    return redirect(url_for('/'))


# Url Admin
@app.route(prefix_admin+'/dashboard', endpoint=startpoint_admin+'/dashboard')
@is_login
def dashboard():
    return DashboardCtl.index()


@app.route(prefix_admin+'/yourself', endpoint=startpoint_admin+'/yourself')
@is_login
def yourself():
    return YourselfCtl.index()


@app.route(prefix_admin+'/project', endpoint=startpoint_admin+'/project')
@is_login
def project():
    return ProjectCtl.index()


@app.route(prefix_admin+'/project/task', endpoint=startpoint_admin+'/project/task')
@is_login
def tasks():
    return ProjectCtl.task()


@app.route(prefix_admin+'/project/task/subtask', endpoint=startpoint_admin+'/project/task/subtask')
@is_login
def subtask():
    return ProjectCtl.subtask()


@app.route(prefix_admin+'/project/task/issue', endpoint=startpoint_admin+'/project/task/issue')
@is_login
def issue():
    return ProjectCtl.bug()


@app.route('/test')
def test():
    return render_template('test.html')

app.secret_key = '\xb2<\xf2\xc5hfg\xed\xb7:\xecH\x05/hJ\x93\xb2\xf5\xdb\xc9\r\x92\xe4'
if __name__ == '__main__':
    app.run()
