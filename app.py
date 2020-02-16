import os

from flask import Flask, request, session, send_from_directory
from flask_cors import CORS
from functools import wraps
from werkzeug.utils import secure_filename
import json
from DatabaseAPI_User import UserAPI
from DatabaseAPI_Video import VideoAPI
from Exceptions import vException
import Utils
import VideoImportTool

app = Flask(__name__)
app.secret_key = ' A\xcd!x\xa6a\xffS\xcc\xc9\xdf?\x15\xd7\xbb\xdf\x0b\x9f\x1cy\xdcb\x8b'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
CORS(app)

def json_response(func):
    @wraps(func)
    def decorated(*args, **kwargs) -> str:
        res = {
            "code": 0,
            "msg": ""
        }
        data = None
        try:
            data = func(*args, **kwargs)
        except vException as e:
            res["code"] = e.args[0]
            res["msg"] = e.args[1]

        if data is not None:
            res.update({
                "data": data
            })
        return json.dumps(res, default=str, ensure_ascii=False)

    return decorated


@app.route("/")
@json_response
def index():
    if "account" in session:
        return "logged in as " + str(session["account"]["username"])
    else:
        return "you are not logged in"


def isLogin():
    if "account" in session:
        return True
    else:
        return False


@app.route("/register", methods=['GET', 'POST'])
@json_response
def user_register():
    if "username" in request.form and "email" in request.form and "password" in request.form:
        try:
            reg_result = UserAPI.UserRegister(
                username=request.form["username"],
                email=request.form["email"],
                pwd=request.form["password"]
            )
        except vException as e:
            raise e
    else:
        raise vException(-1, "Invalid args. Arguments: username email password are required.")


@app.route("/login", methods=['GET', 'POST'])
@json_response
def user_login():
    if "username" in request.form and "password" in request.form:
        try:
            login_result = UserAPI.UserLogin(
                username=request.form["username"],
                pwd=request.form["password"]
            )
        except vException as e:
            raise e

        session["account"] = login_result
        session["isLogin"] = True

        return login_result
    else:
        raise vException(-1, "Invalid args. Arguments: username password are required.")


@app.route("/logout")
@json_response
def user_logout():
    session.clear()
    return True


@app.route("/login-state")
@json_response
def get_login_state():
    if "account" in session:
        return session["account"]
    else:
        raise vException(-1, "Please login.")


@app.route("/check-usability")
@json_response
def check_usability():
    rValue = {}
    if "username" in request.args:
        userExists = UserAPI.CheckUsernameExists(request.args.get("username"))
        rValue.update({
            "username": not userExists
        })
    if "email" in request.args:
        emailExists = UserAPI.CheckEmailExists(request.args.get("email"))
        rValue.update({
            "email": not emailExists
        })
    return rValue


@app.route("/video-url")
@json_response
def get_video_url():
    if "vid" in request.args:
        try:
            urls = VideoAPI.GetVideoUrls(request.args.get("vid"))
            urlsOut = {}
            for url in urls:
                urlsOut.update({url.name: url.url})
            return urlsOut
        except vException as e:
            raise e
    else:
        raise vException(-1, "Invalid args. Argument: Vid is required.")


@app.route("/video-thumbnail")
@json_response
def get_video_thumbnail():
    if "vid" in request.args:
        thumbnail = VideoAPI.GetVideoThumbnail(request.args.get("vid"))
        return thumbnail
    else:
        raise vException(-1, "Invalid args. Argument: Vid is required")


@app.route("/video-list")
@json_response
def get_video_list():
    count = 20
    page = 1
    if "count" in request.args:
        count = request.args.get("count")
    if "page" in request.args:
        page = request.args.get("page")
    data = VideoAPI.GetVideoList(count, page)
    infoOut = []
    for info in data:
        infoDict = info.toDict()
        author = UserAPI.GetUserInfo(infoDict["author"])
        videoThumbnail = VideoAPI.GetVideoThumbnail(info.vid)
        infoDict.update({
            "thumbnail": videoThumbnail["url"],
            "author": author
        })
        infoOut.append(infoDict)
    return infoOut


@app.route("/video-info")
@json_response
def get_video_info():
    count = 20
    if "vid" in request.args:
        data = VideoAPI.GetVideoInfo(request.args["vid"])
        try:
            videoThumbnail = VideoAPI.GetVideoThumbnail(data.vid)
        except vException as ex:
            videoThumbnail = {}
        videoUrls = VideoAPI.GetVideoUrls(data.vid)
        authorInfo = UserAPI.GetUserInfo(data.author)
        authorInfo.pop("email")

        followState = False
        likeState = False
        starState = False
        if "account" in session:
            uid_str = str(session["account"]["uid"])
            vid_str = str(data.vid)
            followState = UserAPI.CheckFollowState(uid_str, str(authorInfo["uid"]))
            likeState = VideoAPI.CheckLikeState(uid_str, vid_str)
            starState = VideoAPI.CheckStarState(uid_str, vid_str)

        data = data.toDict()
        urls = []
        for url in videoUrls:
            urls.append(url.toDict())

        authorInfo.update({
            "isFollow": followState,
        })

        data.update({
            "thumbnail": videoThumbnail["url"],
            "urls": urls,
            "author": authorInfo,
            "isLike": likeState,
            "isStar": starState
        })
        return data
    else:
        raise vException(-1, "Invalid args. Argument: Vid is required")


@app.route("/video-play")
@json_response
def video_play():
    if "vid" in request.args:
        VideoAPI.PlayVideo(request.args.get("vid"))
        return True


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/user-info")
@json_response
def user_info():
    if "uid" in request.args:
        info = UserAPI.GetUserInfo(request.args.get("uid"))
        info.pop("email")
        followInfo = UserAPI.GetUserFollowCount(request.args.get("uid"))
        info.update(
            followInfo
        )
        return info
    else:
        raise vException(-1, "Invalid args. Argument: Uid is required")


@app.route("/description-modify")
@json_response
def change_description():
    if "description" in request.args:
        if len(request.args.get("description")) <= 30:
            UserAPI.ChangeDescription(str(session["account"]["uid"]), request.args.get("description"))
            session["account"]["description"] = request.args.get("description")
            return request.args.get("description")
        else:
            raise vException(-2, "Description is too long")
    else:
        raise vException(-1, "Invalid args. Argument: description is required")


@app.route('/avatar-upload', methods=['POST'])
@json_response
def upload_avatar():
    if "account" in session:
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                raise vException(-1, "File not found")
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                raise vException(-2, "Filename is empty.")
            if file and allowed_file(file.filename):
                ext = file.filename.split('.')[-1]
                random_filename = Utils.gen_str()
                file_name = random_filename + "." + ext
                file.save(os.path.join("static/avatar", file_name))
                UserAPI.ChangeAvatar(str(session["account"]["uid"]), "/avatar/" + file_name)
                session["account"]["avatar"] = "/avatar/" + file_name
                session.modified = True
                return {
                    "avatar": "/avatar/" + file_name
                }
    else:
        raise vException(-3, "Please logged in.")


@app.route("/user-follow")
@json_response
def user_follow():
    if "uid" in request.args and "follow" in request.args:
        if request.args.get("follow") == "true":
            UserAPI.Follow(str(session["account"]["uid"]), request.args.get("uid"))
        else:
            UserAPI.UnFollow(str(session["account"]["uid"]), request.args.get("uid"))
    else:
        raise vException(-1, "Invalid args. Argument: uid, follow is required")


@app.route("/user-like")
@json_response
def user_like():
    if "vid" in request.args and "like" in request.args:
        if request.args.get("like") == "true":
            VideoAPI.Like(str(session["account"]["uid"]), request.args.get("vid"))
        else:
            VideoAPI.UnLike(str(session["account"]["uid"]), request.args.get("vid"))
    else:
        raise vException(-1, "Invalid args. Argument: vid, like is required")


@app.route("/user-star")
@json_response
def user_star():
    if "vid" in request.args and "star" in request.args:
        if request.args.get("star") == "true":
            VideoAPI.Star(str(session["account"]["uid"]), request.args.get("vid"))
        else:
            VideoAPI.UnStar(str(session["account"]["uid"]), request.args.get("vid"))
    else:
        raise vException(-1, "Invalid args. Argument: vid, star is required")


@app.route("/video-comments")
@json_response
def show_comments():
    count = "30"
    page = "1"
    if "vid" in request.args:
        if "count" in request.args:
            if request.args.get("count").isdecimal():
                count = request.args.get("count")
        if "page" in request.args:
            if request.args.get("page").isdecimal():
                page = request.args.get("page")
        commentsInfo = VideoAPI.ShowComment(request.args.get("vid"), count, page)
        comments = []
        for c in commentsInfo:
            comment = c
            userInfo = UserAPI.GetUserInfo(str(c["uid"]))
            userInfo.pop("email")
            comment.update({
                "user": userInfo
            })
            comments.append(comment)
        return comments
    else:
        raise vException(-1, "Invalid args. Argument: vid is required")


@app.route("/send-comment")
@json_response
def add_comment():
    if "account" in session:
        if "vid" in request.args and "text" in request.args:
            if len(request.args.get("text")) <= 300:
                VideoAPI.AddComment(request.args.get("vid"), str(session["account"]["uid"]), "-1", request.args.get("text"))
            else:
                raise vException(-3, "Comment is too long")
        else:
            raise vException(-2, "Invalid args. Arguments: vid, text is required")
    else:
        raise vException(-1, "Please login")


@app.route("/videos/<path:path>")
def send_video(path):
    return send_from_directory("static/videos", path)


@app.route("/video_thumbnail/<path:path>")
def send_video_thumbnail(path):
    return send_from_directory("static/video_thumbnail", path)


@app.route("/avatar/<path:path>")
def send_avatar(path):
    return send_from_directory("static/avatar", path)


with app.test_request_context():
    pass

if __name__ == '__main__':
    app.run()
