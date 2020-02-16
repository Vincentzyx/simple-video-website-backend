from typing import List, Tuple
from functools import wraps
import SqlHelper
import Utils
from Exceptions import vException


def param_sql_escape(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        newArgs = []
        newkwArgs = {}
        for arg in args:
            newArgs.append(Utils.sqlEscapeStr(arg))
        for key in kwargs:
            newkwArgs.update({key: Utils.sqlEscapeStr(kwargs[key])})
        result = func(*newArgs, **newkwArgs)
        return result

    return decorated


class UserAPI:

    @staticmethod
    def UserLogin(username: str, pwd: str) -> str:
        escapedUsername = Utils.sqlEscapeStr(username)
        data = SqlHelper.fetchOne(
            "SELECT password, uid, username, email, avatar, description, joindate, userlevel FROM user WHERE username = '%s' OR email = '%s'" % (
            escapedUsername, escapedUsername))
        if data is not None and len(data) > 0:
            if data[0] == Utils.md5_vsalt(pwd):
                return {
                    "uid": data[1],
                    "username": data[2],
                    "email": data[3],
                    "avatar": data[4],
                    "description": data[5],
                    "joindate": data[6],
                    "userlevel": data[7]
                }
            else:
                raise vException(-10, "Wrong username or password.")
        else:
            raise vException(-10, "Wrong username or password.")

    @staticmethod
    @param_sql_escape
    def CheckUsernameExists(username: str) -> bool:
        data = SqlHelper.fetchOne("SELECT username FROM user WHERE username = '%s'" % username)
        if data is not None and len(data) > 0:
            return True
        else:
            return False

    @staticmethod
    @param_sql_escape
    def CheckEmailExists(email: str) -> bool:
        data = SqlHelper.fetchOne("SELECT username FROM user WHERE email = '%s'" % email)
        if data is not None and len(data) > 0:
            return True
        else:
            return False

    @staticmethod
    def UserRegister(username: str, email: str, pwd: str):
        if not UserAPI.CheckUsernameExists(username):
            if not UserAPI.CheckEmailExists(email):
                escapedUsername = Utils.sqlEscapeStr(username)
                escapedEmail = Utils.sqlEscapeStr(email)
                md5Pwd = Utils.md5_vsalt(pwd)
                result = SqlHelper.execute(
                    "INSERT INTO user (username,email,password,avatar) VALUES ('%s', '%s', '%s', '%s')" % (
                    escapedUsername, escapedEmail, md5Pwd, "avatar/default_avatar.png"))
                if not result:
                    raise vException(-30, "Register failed for unexpected reason.")
            else:
                raise vException(-20, "Email is being used.")
        else:
            raise vException(-10, "Username is being used.")

    @staticmethod
    @param_sql_escape
    def GetUserInfo(uid: str):
        result = SqlHelper.fetchOne(
            "SELECT uid,username,email,avatar,description,joindate FROM user WHERE uid=%s" % uid)
        followInfo = UserAPI.GetUserFollowCount(uid)
        if result is not None:
            return {
                "uid": result[0],
                "username": result[1],
                "email": result[2],
                "avatar": result[3],
                "description": result[4],
                "joindate": result[5],
                "follower": followInfo["follower"],
                "following": followInfo["following"]
            }
        else:
            raise vException(-1, "User not exist.")

    @staticmethod
    @param_sql_escape
    def GetUserFollowCount(uid: str):
        result = SqlHelper.fetchAll("SELECT COUNT(*) FROM `follower` WHERE fromuser='%s' "
                                    "UNION ALL SELECT COUNT(*) FROM `follower` WHERE touser='%s'" % (uid, uid))
        if len(result) == 2:
            return {
                "following": result[0][0],
                "follower": result[1][0]
            }
        else:
            raise vException(-10, "Unexpected error")

    @staticmethod
    @param_sql_escape
    def ChangeAvatar(uid: str, avatar: str):
        result = SqlHelper.execute("UPDATE user SET avatar='%s' WHERE uid=%s" % (avatar, uid))
        if result is not True:
            raise vException(-10, "Unknown error.")

    @staticmethod
    @param_sql_escape
    def ChangeDescription(uid: str, description: str):
        result = SqlHelper.execute("UPDATE user SET description='%s' WHERE uid='%s'" % (description, uid))
        if result is not True:
            raise vException(-10, "Unknown error.")

    @staticmethod
    @param_sql_escape
    def CheckFollowState(fromUid: str, toUid: str):
        followResult = SqlHelper.fetchAll("SELECT * FROM follower WHERE fromuser=%s AND touser=%s" % (fromUid, toUid))
        if len(followResult) > 0:
            return True
        else:
            return False

    @staticmethod
    @param_sql_escape
    def Follow(fromUid: str, toUid: str):
        result = SqlHelper.fetchAll("SELECT * FROM follower WHERE fromuser=%s AND touser=%s" % (fromUid, toUid))
        if len(result) == 0:
            result = SqlHelper.execute("INSERT INTO follower (fromuser,touser,time) VALUES (%s,%s,'%s')" % (fromUid, toUid, Utils.time_str()))
            return True
        else:
            raise vException(-10, "不能重复关注")

    @staticmethod
    @param_sql_escape
    def UnFollow(fromUid: str, toUid: str):
        result = SqlHelper.execute("DELETE FROM follower WHERE fromuser=%s AND touser=%s" % (fromUid, toUid))
        return True


