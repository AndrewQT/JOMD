import sqlite3
from util import constants
from util.problem import Problem
from util.submission import Submission


class DbConn:
    def __init__(self):
        self.conn = sqlite3.connect(constants.DB_DIR)
        self.init_tables()

    def init_tables(self):
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS problems ('
            'code                       TEXT PRIMARY KEY,'
            'name                       TEXT,'
            'types                      TEXT,'
            'category                   TEXT,'
            'time_limit                 REAL,'
            'memory_limit               INTEGER,'
            'points                     REAL,'
            'is_partial                 BOOLEAN,'
            'is_organization_private    BOOLEAN,'
            'is_public                  BOOLEAN'
            ')'
        )

        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS submissions ('
            'id             INTEGER PRIMARY KEY,'
            'problem        TEXT,'
            'user           TEXT,'
            'date           DATE,'
            'language       TEXT,'
            'time           REAL,'
            'memory         REAL,'
            'points         REAL,'
            'result         TEXT'
            ')'
        )

    def _update_many(self, query, args):
        rc = self.conn.executemany(query, args).rowcount
        self.conn.commit()
        return rc

    def _update_one(self, query, arg):
        rc = self.conn.execute(query, arg).rowcount
        self.conn.commit()
        return rc
    
    def _fetchall(self, query, args):
        return self.conn.execute(query, args).fetchall()

    def _fetchone(self, query, arg):
        return self.conn.execute(query, arg).fetchone()

    def cache_problem(self, problem):
        query = ('INSERT OR REPLACE INTO problems VALUES'
                 '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        self._update_one(query, tuple(problem))

    def cache_problems(self, problems):
        query = ('INSERT OR REPLACE INTO problems VALUES'
                 '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        problems = map(tuple, problems)
        self._update_many(query, problems)

    def cache_submissions(self, submissions):
        query = ('INSERT OR REPLACE INTO submissions VALUES'
                 '(?, ?, ?, ?, ?, ?, ?, ?, ?)')
        submissions = map(tuple, submissions)
        self._update_many(query, submissions)

    def get_problem(self, code, conditions={}):
        query = ('SELECT * FROM problems WHERE '
                 'code = ?')
        query = add_conditions(query, 'problems',conditions)
        res = self._fetchone(query, (code,))
        return Problem(res)

    def get_submissions(self, username):
        query = ('SELECT * FROM submissions WHERE '
                 'user = ?')
        res = self._fetchall(query, (username,))
        return list(map(Submission, res))

    def get_solved_problems(self, username):
        query = ('SELECT problem.* FROM '
                 'problems problem LEFT JOIN '
                 '(SELECT problem, max(points) points FROM submissions WHERE user=? GROUP BY problem) '
                 'submission ON submission.problem = problem.code WHERE '
                 'ifnull(submission.points, 0) == problem.points')
        res = self._fetchall(query, (username,))
        return list(map(Problem, res))

    def get_solved_problems_type(self, username, types):
        query = ('SELECT problem.* FROM '
                 'problems problem LEFT JOIN '
                 '(SELECT problem, max(points) points FROM submissions WHERE user=? GROUP BY problem) '
                 'submission ON submission.problem = problem.code WHERE '
                 'ifnull(submission.points, 0) == problem.points AND '
                 'problem.types like ?')
        types = str_to_like(types)
        res = self._fetchall(query, (username, types,))
        return list(map(Problem, res))

    def get_solved_problems_types(self, username, types):
        query = ('SELECT problem.* FROM '
                 'problems problem LEFT JOIN '
                 '(SELECT problem, max(points) points FROM submissions WHERE user=? GROUP BY problem) '
                 'submission ON submission.problem = problem.code WHERE '
                 'ifnull(submission.points, 0) == problem.points AND (')
        query += ' OR '.join(['problem.types like ?'] * len(types))+')'
        types = map(str_to_like, types)
        args = (username, *types,)
        res = self._fetchall(query, args)
        return list(map(Problem, res))

    def get_unsolvedproblems(self, username, low=0, high=50):
        query = ('SELECT problem.* FROM '
                 'problems problem LEFT JOIN '
                 '(SELECT problem, max(points) points FROM submissions WHERE user=? GROUP BY problem) '
                 'submission ON submission.problem = problem.code WHERE '
                 'ifnull(submission.points, 0) < problem.points AND '
                 '(problem.points BETWEEN ? AND ?)')
        args = (username, low, high,)
        res = self._fetchall(query, args)
        return list(map(Problem, res))

    def get_problem_type(self, types):
        query = ('SELECT * FROM problems WHERE '
                 'problems.types like ?')
        types = str_to_like(types)
        args = (types,)
        res = self._fetchall(query, args)
        return list(map(Problem, res))

    def get_problem_types(self, types):
        query = 'SELECT * FROM problems WHERE '
        query += ' OR '.join(['problems.types like ?'] * len(types))
        types = map(str_to_like, types)
        args = (*types,)
        res = self._fetchall(query, args)
        return list(map(Problem, res))

    def close(self):
        self.conn.close()


def add_query(name, val):
    if val is None:
        return ''
    return f' AND {name} = {val}'

def add_conditions(query, table, conditions):
    for k,v in conditions:
        query += add_query(table+'.'+k, v)
    return query

def str_to_like(types):
    return '%'+types+'%'
