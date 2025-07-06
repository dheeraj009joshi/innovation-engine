
from datetime import datetime
import requests



class ScraperClient:
    
    def __init__(self,token):
        self.token=token
        self.url="https://api.lamatok.com/v1" # define your  the main url here 
    
    def download_video(self,filepath, video_url):

        pass

    def get_transcript_for_video(self,filename):
        pass

    def get_post_details_by_post_id(self, id):
        pass

    def get_hastag_info(self, query):
        try: 
            params = {
            "hashtag":query,
            "access_key":self.token
            } 
            res=requests.get(f"{self.url}/hashtag/info",params=params)
            print(res.json())
            return res.json()
        except Exception as err:
            print(err)
            pass

    def get_hastag_id_by_tag_name(self,tag_name):
        details=self.get_hastag_info(tag_name)
        print(details)
        return details["challengeInfo"]["challenge"]["id"]
    

    def get_hastag_posts_by_id(self,hastag_id, count,progress_callback):
        out=[]
        if progress_callback:
            progress_callback(0, len(out))
        for i in range(2):

            params = {
            "id":hastag_id,
            "count":count,
            "cursor":len(out),
            "access_key":self.token
            } 
            res=requests.get(f"{self.url}/hashtag/medias",params=params)
            print(res.json())
            if "itemList" in res.json():
                for item in res.json()["itemList"]:
                    try:
                        data={}
                        data["description"]=item["desc"]
                        data["id"]=item["id"]
                        data["videoUrl"]=item["video"]["bitrateInfo"][0]["PlayAddr"]["UrlList"][-1]
                        data["user_info"]={
                            "name":item["author"]["nickname"],
                            "bio":item["author"]["signature"],
                            "username":item["author"]["uniqueId"],
                            "followers":item["authorStats"]["followerCount"],
                            "followings":item["authorStats"]["followingCount"],
                            "totalLikes":item["authorStats"]["heart"]
                        }
                        data["createTime"]=datetime.fromtimestamp(item["createTime"]).isoformat()
                        data["collectCount"]=item["stats"]["collectCount"]
                        data["commentCount"]=item["stats"]["commentCount"]
                        data["playCount"]=item["stats"]["playCount"]
                        data["shareCount"]=item["stats"]["shareCount"]
                        out.append(data)
                        if res.json()["hasMore"]==False:
                            break
                    except:
                        pass
            print(len(out)) 
        return out
    

    def get_post_comments_by_post_id(self,postId,count):
        out=[]
        
        try: 
            
            params = {
            "id":postId,
            "count":count,
            "access_key":self.token
            } 
            res=requests.get(f"{self.url}/media/comments/by/id",params=params)
            print(res.json())
            for item in res.json()["comments"]:
                try:
                    data={}
                    data["text"]=item["share_info"]["desc"]
                    out.append(data)
                except:
                    pass 
            return out
        except Exception as err:
            print(err)
            pass



    def get_hastag_posts_by_id_cursor(self,hastag_id, count):
        out=[]
        
        cursor=0
        while int(cursor) < count:

            params = {
            "id":hastag_id,
            "cursor":cursor,
            "access_key":self.token
            } 
            res=requests.get(f"{self.url}/hashtag/medias",params=params)
            print(res.json())
            if "itemList" in res.json():
                cursor= res.json()["cursor"]
                for item in res.json()["itemList"]:
                    try:
                        data={}
                        data["description"]=item["desc"]
                        data["id"]=item["id"]
                        data["videoUrl"]=item["video"]["bitrateInfo"][0]["PlayAddr"]["UrlList"][-1]
                        data["user_info"]={
                            "name":item["author"]["nickname"],
                            "bio":item["author"]["signature"],
                            "username":item["author"]["uniqueId"],
                            "followers":item["authorStats"]["followerCount"],
                            "followings":item["authorStats"]["followingCount"],
                            "totalLikes":item["authorStats"]["heart"]
                        }
                        data["createTime"]=datetime.fromtimestamp(item["createTime"]).isoformat()
                        data["collectCount"]=item["stats"]["collectCount"]
                        data["commentCount"]=item["stats"]["commentCount"]
                        data["playCount"]=item["stats"]["playCount"]
                        data["shareCount"]=item["stats"]["shareCount"]
                        out.append(data)
                        if res.json()["hasMore"]==False:
                            break
                    except:
                        pass
            print(len(out)) 
        return out[:count]
    
    
aa=ScraperClient("1J3SttXjxlZIekKgvbX9sgyWtDQm8Zxh")

# # tt=aa.get_hastag_info("sleep")
# # print(tt)
# res=aa.get_hastag_posts_by_id_cursor(12563,10000)
# print(res)

# res=aa.get_post_comments_by_post_id(7242381942933490971,100)
# print(res)