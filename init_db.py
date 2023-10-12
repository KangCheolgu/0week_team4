from pymongo import MongoClient           # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle                      # 'dbjungle'라는 이름의 db를 만듭니다.


def insert_all():
    
        review = {
            'num' : 0,
            'restaurant': 'initdata',
            'category': 'initdata',
            'comment': 'initdata',
            'like':0,
            'locate':'initdata',
            'user_id':'initdata',
            'favorite':0 ,
            'image': None
        }
        db.review.insert_one(review)

if __name__ == '__main__':
    # 기존의 movies 콜렉션을 삭제하기
    db.review.drop()

    # 영화 사이트를 scraping 해서 db 에 채우기
    insert_all()