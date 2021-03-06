# -*- coding: utf-8 -*-
# Copyright 2017 ProjectV Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask_restful import Resource
from flask import request, g, jsonify
from v.tools.v import tuple2list
from v.tools.exception import ExceptionRest
from v.habit.model.habitMdl import HabitMdl
from v.reminder.controllers.reminderCtl import ReminderCtl

class HabitListRst(Resource, HabitMdl):

    def get(self):
        _get = jsonify()
        try:
            _view = request.args.get("view")
            if not _view:
                data = g.db_conn.execute("select * from %s where user_id='%s' order by id asc;"
                                         % (self._table, g.user.id,))
                if g.db_conn.count() > 0:
                    _get = jsonify(tuple2list(self._fields, data))
                    _get.status_code = 200
                else:
                    raise ExceptionRest(status_code=404)
            elif _view == 'current_task':
                _date = request.args.get("date")
                _get = jsonify(self.current_task(_date))
                _get.status_code = 200
            else:
                raise ExceptionRest(status_code=404)
        except ExceptionRest, e:
            _get.status_code = e.status_code
        return _get

    def current_task (self, _date):
        _timezone_user = " AT TIME ZONE '"+g.user.timezone+"' " if g.user.timezone else ""
        _qrs = """
          SELECT
          d.id,
          d.name,
          '' state,
          (
            SELECT count(id) FROM history_habits tdh1 WHERE
            tdh1.habit_id =d.id and tdh1.user_id =d.user_id and tdh1.state='success'
          ) success
          ,
          CASE WHEN

            (
              (CAST(current_timestamp AS DATE ) - CAST(d.created_date AS DATE )) -
              (SELECT count(id) FROM history_habits tdh1 WHERE tdh1.habit_id =d.id and tdh1.user_id =d.user_id and tdh1.state='success')
            ) >= 0
            THEN
              (
                (CAST(current_timestamp AS DATE ) - CAST(d.created_date AS DATE )) -
                (SELECT count(id) FROM history_habits tdh1 WHERE tdh1.habit_id =d.id and tdh1.user_id =d.user_id and tdh1.state='success')
              )
            ELSE
              0
            END fail
        FROM habits d LEFT JOIN history_habits dh
            ON d.id =dh.habit_id AND d.user_id = dh.user_id
            and CAST(dh.created_date AT TIME ZONE 'UTC' %s AS DATE) = '%s'
        where
          d.closed_date IS NULL
          and d.user_id = %s
          and dh.id is NULL;
        ;""" % (_timezone_user, _date, g.user.id)
        _current_task = []
        _data = g.db_conn.execute(_qrs)
        if g.db_conn.count() > 0:
            _current_task = tuple2list(['id', 'name', 'status', 'success', 'fail'], _data)
        else:
            raise ExceptionRest(status_code=404)
        return _current_task

    def post(self):
        _data = request.json
        _insert = []
        _post = _insert
        qri = "insert into %s (user_id, name) values(%s,'%s') returning id;" \
              % (self._table, g.user.id, _data.get('name'))
        g.db_conn.execute(qri)
        if g.db_conn.count() > 0:
            _new_habit_id = g.db_conn.one()[0]
            _insert.append({"id": _new_habit_id})
            params = {
                'create_id': g.user.id,
                'resource': 'habit',
                'resource_id': _new_habit_id,
                'every': 1,
                'by': 'daily'
            }
            ReminderCtl.insert(g.db_conn, params)
        _post = jsonify(_insert)
        return _post


class HabitRst(Resource, HabitMdl):

    def get(self, habit_id):
        data = g.db_conn.execute('select * from %s where user_id =%s and id = %s;'
                                 % (self._table, g.user.id, str(habit_id)))
        _get = tuple2list(self._fields, data)
        r = jsonify(_get)
        if len(_get) <= 0:
            r.status_code = 404
        else:
            r.status_code = 200
        return r

    def delete(self, habit_id):
        qrd = "delete from %s where user_id=%s and id=%s" % (self._table, g.user.id, habit_id)
        _data = g.db_conn.execute(qrd)
        _delete = jsonify()
        if g.db_conn.count() > 0:
            _delete.status_code = 200
        else:
            _delete.status_code = 404
        return _delete

    def put(self, habit_id):
        _data = request.json
        _put = jsonify()
        # print _data
        qru = "update  %s set name ='%s' where user_id=%s and id = %s" % \
              (self._table, _data.get('name'), g.user.id, habit_id)
        g.db_conn.execute(qru)
        if g.db_conn.count() > 0:
            _put.status_code = 200
        else:
            _put.status_code = 404
        return _put
