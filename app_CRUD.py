from bson.objectid import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

# from bs4 import BeautifulSoup

import json


app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle

#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의된 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못해도 그냥 넘어갈 코드입니다.
# #####################################################################################

# list(db.review.find({'id': id}))

# 부모 index.html을 상속하는 3가지 자식 템플릿 post.html | mydetail.html | otherdetail.html
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/post')
def post():
    review=db.review.find_one({'user_id':'test'})
    return render_template('post.html', category=category, review=review)


category={'한식', '중식', '일식', '양식'}
@app.route('/mydetail')
def my_detail():
    review=db.review.find_one({'user_id':'test'})
    return render_template('mydetail.html', review=review)

@app.route('/mydetail_modifying')
def modifying_detail():
    review=db.review.find_one({'user_id':'test'})
    return render_template('mydetail_modifying.html', review=review, category=category)

@app.route('/otherdetail')
def other_detail():
    review=db.review.find_one({'user_id': 'test'})
    likes=review['like']
    
    return render_template('otherdetail.html',likes=likes, review=review)


# 맛집 리뷰 POST
@app.route('/post/mydetail', methods=['POST'])
def post_my_detail():
   # 1. 클라이언트로부터 데이터를 받기
    restaurant_receive=request.form['restaurant_give']
    category_receive=request.form['category_give']
    print(category_receive)
    comment_receive=request.form['comment_give']
   #  이미지 받기

    # 예외 처리
    if restaurant_receive=="" or comment_receive=="" or category_receive=="선택하기":
       return jsonify({'result':'empty'})

    # 2. document 만들기 (TEST)
    review = {'restaurant': restaurant_receive, 'category': category_receive, 'comment': comment_receive, 'like':0, 'locate':'kyeongki', 'name':'jungler','rate':5,'user_id':'test', 'favorite':0 }
   # 카테고리와 이미지 추가 필요

    # 3. mongoDB에 데이터 넣기
    db.review.insert_one(review)

    return jsonify({'result':'success'})

@app.route('/modify/mydetail',methods=['POST'])
def modify_my_detail():
    # 1. 클라이언트로부터 데이터를 받기
    restaurant_receive=request.form['restaurant_give']
    category_receive=request.form['category_give']
    comment_receive=request.form['comment_give']
    # id_receive=request.form['id_give']
    # 이미지 받기

    # 예외 처리1: 빈칸으로 수정할 때
    if restaurant_receive=="" or comment_receive=="" or category_receive=="선택하기":
       return jsonify({'result':'empty'})


    # 예외 처리2: 아무것도 수정하지 않았을 때 
    flag = True # 무엇인가 최소 하나 수정한 상태를 전제로
    changed_or_not = db.review.find_one({'user_id': 'test3'})
    if changed_or_not['restaurant']==restaurant_receive and changed_or_not['comment']==comment_receive and changed_or_not['category']==category_receive:
       flag = False # 아무것도 수정하지 않았다.

    result = db.review.update_one({'user_id': 'test3'},{'$set': {'restaurant': restaurant_receive, 'category':category_receive, 'comment': comment_receive, }})
    # DB 아이디 쓰는 경우: '_id': ObjectId(id_receive)
    # 이미지 추가 필요

    print(result.modified_count)
    print(flag)
    if result.modified_count == 1 and flag: # 수정한 document가 1개이고, 무엇인가 최소 하나 수정한 상태라면 성공
      return jsonify({'result': 'success'})
    else: # 수정한 document가 1이 아니거나, 아무것도 수정되지 않은 경우 실패
      return jsonify({'result': 'failure'})

@app.route('/like',methods=['POST'])
def like_review():
    # id_receive = request.form['id']
    # review = db.review.find_one({'_id': ObjectId(id_receive)})
    print("test")
    review=db.review.find_one({'user_id':'test'})
    new_likes = review['like'] + 1
    result = db.review.update_one({'user_id':'test'}, {'$set': {'like': new_likes}})
    print(review['like'])
    # 4. 하나의 메모만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success 를 보냄
    if result.modified_count == 1:
       return jsonify({'result': 'success'})
    else:
       return jsonify({'result': 'failure'})

@app.route('/favorite',methods=['POST'])
def favorite_review():
    # id_receive = request.form['id']
    review=db.review.find_one({'user_id':'test'})
    print(review)
   
    # 이미 즐겨찾기 되어있을 때
    if review['favorite']==0:
       result = db.review.update_one({'user_id':'test'}, {'$set': {'favorite':1 }})
    elif review['favorite']==1:
       return jsonify({'result':'existed'})

    if result.modified_count == 1:
      return jsonify({'result': 'success'})
    else:
      return jsonify({'result': 'failure'})
    
@app.route('/delete',methods=['POST'])
def delete_review():
    # id_receive = request.form['id']
    # result = db.review.delete_one({'_id': ObjectId(id_receive)})

    result = db.review.delete_one({'user_id':'123abc'})
    # 3. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success 를 보냄
    if result.deleted_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})

# 새로운 리뷰 포스트하기
# @app.route('/review/post', methods=['POST'])
# def post_review():
#     # 1. 클라이언트로부터 데이터를 받기
#     restaurant_receive=request.form['restaurant_give']
#     #  category_receive=request.form['category_give']
#     review_receive=request.form['review_give']


#     # 예외 처리
#     if restaurant_receive=="" or review_receive=="":
#        return jsonify({'result':'empty'})

#     # 2. document 만들기
#     review = {'restaurant': restaurant_receive, 'review': review_receive}    

#     # 3. mongoDB에 데이터 넣기
#     db.review.insert_one(review)

#     return jsonify({'result':'success'})

# @app.route('/review/mydetail', methods=['GET'])
# def read_mydetail():
#    #  sortMode = request.args.get('sortMode', 'likes')

#    post = db.review.find({'id':id})
#    restaurant = post.restaurant
#    review = post.review
#    if restaurant !='' and review !='':
#        return jsonify({'result': 'success'})

#    else:
#         return jsonify({'result': 'failure'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5005, debug=True)
