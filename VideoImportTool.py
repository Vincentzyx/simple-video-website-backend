import os
import cv2
import Utils
from DatabaseAPI_Video import VideoAPI
import SqlHelper


def doImport(vidLink: str):
    for root,dirs,files in os.walk(vidLink):
        for file in files:
            fname = str(file)
            vname = fname.replace(".mp4", "")
            print(vname)
            vid = VideoAPI.AddVideo("Admin", vname, "From bilibili for testing2\n" + vname, "测试,test,bilibili,短视频")
            url_name = Utils.md5(vname)
            get_video_pic(vidLink + "\\" + file, r"static\video_thumbnail\%s.jpg" % url_name)
            VideoAPI.AddVideoThumbnail(str(vid), url_name, "video_thumbnail/" + url_name + ".jpg")
            os.rename(vidLink + "\\" + file, vidLink + "\\" + url_name + ".mp4")
            VideoAPI.AddVideoUrl(str(vid), "标清", "videos/" + url_name + ".mp4")

def doUpdate(vidLink: str):
    data = SqlHelper.fetchAll("SELECT vid,name,url FROM video_url")
    for line in data:
        SqlHelper.execute("UPDATE video_url SET url='%s' WHERE vid='%s'" % (line[2].replace(".mp4.mp4", ".mp4"), line[0]))


def doGetThumbnail(vidLink: str):
    for root,dirs,files in os.walk(vidLink):
        for file in files:
            fname = str(file)
            vname = fname.replace(".mp4", "")
            print(vname)
            url_name = vname
            try:
                vid = VideoAPI.FindVideoByName(url_name)
                get_video_pic(r"static\videos\%s.mp4" % vname, r"static\video_thumbnail\%s.jpg" % vname)
                VideoAPI.AddVideoThumbnail(str(vid), url_name, "video_thumbnail/" + url_name + ".jpg")
            except Exception:
                pass


def get_video_pic(name, dest):
    cap = cv2.VideoCapture(name)
    cap.set(1, int(cap.get(7)/2)) # 取它的中间帧
    rval, frame = cap.read() # 如果rval为False表示这个视频有问题，为True则正常
    if rval:
        cv2.imwrite(dest, frame)  # 存储为图像
    cap.release()