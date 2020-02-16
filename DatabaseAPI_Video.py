from typing import List, Tuple
from functools import wraps
import datetime
import SqlHelper
import Utils
from Exceptions import vException


def param_sql_escape(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        newArgs = []
        newkwArgs = {}
        for arg in args:
            if arg is str:
                newArgs.append(Utils.sqlEscapeStr(arg))
            else:
                newArgs.append(arg)
        for key in kwargs:
            if kwargs[key] is str:
                newkwArgs.update({key: Utils.sqlEscapeStr(kwargs[key])})
            else:
                newkwArgs.update({key: kwargs[key]})
        result = func(*newArgs, **newkwArgs)
        return result

    return decorated


class VideoAPI:
    class VideoInfo:

        vid = ""
        author = ""
        title = ""
        description = ""
        tags = ""
        view = ""
        publishdate = datetime.datetime.now()
        modifydate = datetime.datetime.now()
        danmaku = 0
        like = 0
        star = 0
        share = 0

        def __init__(self, _vid="", _author="", _title="", _description="", _tags="", _publishdate=None,
                     _modifydate=None, _view=0, _danmaku=0, _like=0, _star=0, _share=0):
            self.vid = _vid
            self.author = _author
            self.title = _title
            self.description = _description
            self.tags = _tags
            if _publishdate is not None:
                self.publishdate = _publishdate
            if _modifydate is not None:
                self.modifydate = _modifydate
            self.view = _view
            self.danmaku = _danmaku
            self.like = _like
            self.star = _star
            self.share = _share

        def bind(self, info):
            if len(info) == 12:
                self.vid = info[0]
                self.author = info[1]
                self.title = info[2]
                self.description = info[3]
                self.tags = info[4]
                self.publishdate = info[5]
                self.modifydate = info[6]
                self.view = info[7]
                self.danmaku = info[8]
                self.like = info[9]
                self.star = info[10]
                self.share = info[11]
            else:
                raise vException(-10, "Binding error.")

        def toDict(self):
            return {
                "vid": self.vid,
                "author": self.author,
                "title": self.title,
                "description": self.description,
                "tags": self.tags,
                "publishdate": self.publishdate,
                "modifydate": self.modifydate,
                "view": self.view,
                "danmaku": self.danmaku,
                "like": self.like,
                "star": self.star,
                "share": self.share
            }

    @staticmethod
    @param_sql_escape
    def GetVideoInfo(vid: str) -> VideoInfo:
        if type(vid) is int or vid.isdecimal():
            data = SqlHelper.fetchAll(
                "SELECT `vid`, `author`, `title`, `description`, `tags`, `publishdate`, `modifydate`, "
                "`view`, `danmaku`, `like`, `star`, `share` FROM video "
                "WHERE `vid` = %s" % vid)
            if len(data) > 0:
                info = data[0]
                vinfo = VideoAPI.VideoInfo()
                vinfo.bind(info)
                return vinfo
            else:
                raise vException(-2, "Video not exist.")
        else:
            raise vException(-1, "VID invalid.")

    class VideoUrl:

        vid = ""
        name = ""
        url = ""

        def __init__(self, _vid, _name, _url):
            self.vid = _vid
            self.name = _name
            self.url = _url

        def toDict(self):
            return {
                "vid": self.vid,
                "name": self.name,
                "url": self.url
            }

    @staticmethod
    @param_sql_escape
    def GetVideoUrls(vid: str) -> List[VideoUrl]:
        if type(vid) is int or vid.isdecimal():
            data = SqlHelper.fetchAll("SELECT vid, name, url FROM video_url WHERE vid = %s" % vid)
            if len(data) > 0:
                urls = []
                for url in data:
                    urls.append(VideoAPI.VideoUrl(
                        _vid=url[0],
                        _name=url[1],
                        _url=url[2]
                    ))
                return urls
            else:
                raise vException(-2, "Video url not exist.")
        else:
            raise vException(-1, "Invalid vid.")

    @staticmethod
    @param_sql_escape
    def AddVideo(author: str, title: str, description: str, tags: str) -> str:
        datetimeStr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = SqlHelper.insert("INSERT INTO video (author, title, description, tags, publishdate, modifydate) "
                                "VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (
                                author, title, description, tags, datetimeStr, datetimeStr))
        return data

    @staticmethod
    @param_sql_escape
    def AddVideoUrl(vid: str, name: str, url: str):
        if type(vid) is int or vid.isdecimal():
            vInfo = SqlHelper.fetchAll(
                "SELECT vid FROM video WHERE vid = %s" % vid)
            if len(vInfo) > 0:
                vUrls = SqlHelper.fetchAll("SELECT vid,name,url FROM video_url WHERE vid = %s" % vid)
                if len(vUrls) == 0:
                    SqlHelper.execute(
                        "INSERT INTO video_url (vid, name, url) VALUES (%s, '%s', '%s')" % (vid, name, url))
                else:
                    for svid, sname, surl in vUrls:
                        print(svid, sname, surl)

            else:
                raise vException(-2, "Video not exist.")
        else:
            raise vException(-1, "Invalid vid.")

    @staticmethod
    @param_sql_escape
    def GetVideoList(count: str = "30", page: str = "0") -> List[VideoInfo]:
        if type(count) is int or count.isdecimal():
            count = int(count)
            page = int(page)
            count = 40 if count > 40 else count
            data = SqlHelper.fetchAll("SELECT `vid`, `author`, `title`, `description`, `tags`, `publishdate`, "
                                      "`modifydate`, `view`, `danmaku`, `like`, `star`, `share` "
                                      "FROM `video` ORDER BY `vid` DESC LIMIT %d,%d" % ((page-1)*count, count))
            vlist = []
            for info in data:
                vinfo = VideoAPI.VideoInfo()
                vinfo.bind(info)
                vlist.append(vinfo)
            return vlist
        else:
            raise vException(-1, "Invalid count.")


    @staticmethod
    @param_sql_escape
    def GetVideoThumbnail(vid: str):
        if type(vid) is int or vid.isdecimal():
            data = SqlHelper.fetchAll("SELECT `vid`, `pkey`, `url` FROM `video_thumbnail` WHERE `vid` = %s" % vid)
            if len(data) > 0:
                info = data[0]
                return {
                    "vid": info[0],
                    "pkey": info[1],
                    "url": info[2]
                }
            else:
                raise vException(-2, "Video thumbnail not exist.")
        else:
            raise vException(-1, "Invalid vid.")



    @staticmethod
    @param_sql_escape
    def AddVideoThumbnail(vid: str, pkey: str, url: str):
        if type(vid) is int or vid.isdecimal():
            vInfo = SqlHelper.fetchAll(
                "SELECT `vid` FROM `video` WHERE `vid` = %s" % vid)
            if len(vInfo) > 0:
                vUrls = SqlHelper.fetchAll("SELECT `vid`,`pkey`,`url` FROM `video_thumbnail` WHERE `vid` = %s" % vid)
                if len(vUrls) == 0:
                    SqlHelper.execute(
                        "INSERT INTO `video_thumbnail` (`vid`, `pkey`, `url`) VALUES (%s, '%s', '%s')" % (vid, pkey, url))
                else:
                    for svid, sname, surl in vUrls:
                        print(svid, sname, surl)

            else:
                raise vException(-2, "Video not exist.")
        else:
            raise vException(-1, "Invalid vid.")


    @staticmethod
    @param_sql_escape
    def FindVideoByName(name: str) -> int:
        vInfo = SqlHelper.fetchOne("SELECT `vid` FROM `video_url` WHERE `url` = 'videos/%s.mp4'" % name)
        if vInfo is not None:
            return vInfo[0]
        else:
            raise vException(-1, "Video not found.")

    @staticmethod
    @param_sql_escape
    def AddComment(vid: str, uid: str, reply: str, text: str):
        result = SqlHelper.execute("INSERT INTO comment (vid,uid,reply,text,time) VALUES (%s,%s,%s,'%s','%s')"
                                   % (vid, uid, reply, text, Utils.time_str()))
        return True

    @staticmethod
    @param_sql_escape
    def DelComment(fid: str):
        result = SqlHelper.execute("DELETE FROM comment WHERE id=%s" % fid)
        return True

    @staticmethod
    @param_sql_escape
    def ShowComment(vid: str, count: str = "30", page: str = "1"):
        page = int(page)
        count = int(count)
        comments = []
        result = SqlHelper.fetchAll("SELECT id,uid,reply,text,time FROM comment WHERE vid=%s ORDER BY time DESC LIMIT %s,%s"
                                    % (vid, (page-1)*count, count))
        for comment in result:
            comments.append({
                "id": comment[0],
                "uid": comment[1],
                "reply": comment[2],
                "text": comment[3],
                "time": comment[4]
            })
        return comments

    @staticmethod
    @param_sql_escape
    def Like(fromUid: str, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM userlike WHERE likefrom=%s AND liketo=%s" % (fromUid, toVid))
        if len(result) == 0:
            result = SqlHelper.execute("INSERT INTO userlike (likefrom, liketo, time) VALUES (%s, %s, '%s')"
                                        % (fromUid, toVid, Utils.time_str()))
            result = SqlHelper.execute("UPDATE video SET `like`=`like`+1 WHERE vid=%s" % toVid)
            return True
        else:
            raise vException(-10, "不能重复点赞")

    @staticmethod
    @param_sql_escape
    def UnLike(fromUid, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM userlike WHERE likefrom=%s AND liketo=%s" % (fromUid, toVid))
        if len(result) > 0:
            result = SqlHelper.execute("DELETE FROM userlike WHERE likefrom=%s AND liketo=%s" % (fromUid, toVid))
            result = SqlHelper.execute("UPDATE video SET `like`=`like`-1 WHERE vid=%s" % toVid)
            return True
        else:
            raise vException(-10, "你没有点过赞")

    @staticmethod
    @param_sql_escape
    def Star(fromUid: str, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM star WHERE starFrom=%s AND starto=%s" % (fromUid, toVid))
        if len(result) == 0:
            result = SqlHelper.execute("INSERT INTO star (starfrom, starto, time) VALUES (%s, %s, '%s')"
                                        % (fromUid, toVid, Utils.time_str()))
            result = SqlHelper.execute("UPDATE video SET star=star+1 WHERE vid=%s" % toVid)
            return True
        else:
            raise vException(-10, "不能重复收藏");

    @staticmethod
    @param_sql_escape
    def UnStar(fromUid: str, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM star WHERE starFrom=%s AND starto=%s" % (fromUid, toVid))
        if len(result) > 0:
            result = SqlHelper.execute("DELETE FROM star WHERE starfrom=%s AND starto=%s" % (fromUid, toVid))
            result = SqlHelper.execute("UPDATE video SET star=star-1 WHERE vid=%s" % toVid)
            return True
        else:
            raise vException(-10, "你没有收藏过")

    @staticmethod
    @param_sql_escape
    def CheckStarState(fromUid: str, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM star WHERE starfrom=%s AND starto=%s" % (fromUid, toVid))
        if len(result) > 0:
            return True
        else:
            return False

    @staticmethod
    @param_sql_escape
    def CheckLikeState(fromUid: str, toVid: str):
        result = SqlHelper.fetchAll("SELECT * FROM userlike WHERE likefrom=%s AND liketo=%s" % (fromUid, toVid))
        if len(result) > 0:
            return True
        else:
            return False

    @staticmethod
    @param_sql_escape
    def GetStaredVideos(uid: str):
        result = SqlHelper.fetchAll("SELECT starto FROM star WHERE starfrom=%s" % uid)
        staredVideos = []
        if len(result) > 0:
            for vid in result:
                staredVideos.append(vid[0])
        return staredVideos

    @staticmethod
    @param_sql_escape
    def GetLikedVideos(uid: str):
        result = SqlHelper.fetchAll("SELECT liketo FROM userlike WHERE likefrom=%s" % uid)
        likedVideos = []
        if len(result) > 0:
            for vid in result:
                likedVideos.append(vid[0])
        return likedVideos

    @staticmethod
    @param_sql_escape
    def PlayVideo(vid: str):
        result = SqlHelper.execute("UPDATE video set view=view+1 WHERE vid=%s" % vid)
        return True

