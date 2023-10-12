from bson import ObjectId
from pymongo import MongoClient
from bson.json_util import dumps
import json
import jwt
from datetime import datetime,timedelta
import hashlib
import urllib.request
import urllib.error
import time


from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle
      
SECRET_KEY = 'secret_key'

# 첫 페이지
@app.route('/')
def home():
   return render_template('login.html')

@app.route('/join')
def joinpage():
   return render_template('join.html')

@app.route('/mainpage')
def mainpage():
    token_receive = request.cookies.get('mytoken')
    
    rest_list = list(db.dbjungle.find({}, {'_id':False}))

    #받은 토큰을 복호화 한 다음 시간이나 증명에 문제가 있다면 예외처리합니다.
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('card.html', rest_list = rest_list, random_rest = json.dumps(rest_list))
    except jwt.ExpiredSignatureError:
        return redirect("http://localhost:5000/")
    except jwt.exceptions.DecodeError:
        return redirect("http://localhost:5000/")


# 로그인 회원가입 관련
@app.route('/login', methods=['POST'])
def login():
   
    # 아이디 비밀번호를 받는다
    targetId = request.form['targetId']
    targetPwd = request.form['targetPwd']

    pw_hash = hashlib.sha256(targetPwd.encode('utf-8')).hexdigest()

    # DB 안에서 맞는 유저 정보를 찾는다
    targetUser = db.users.find_one({'Id':targetId,'Pwd':pw_hash})
    print(targetUser)
    # 있으면 로그인 성공 없다면 실패처리
    if targetUser == None:
        return jsonify({'result': 'fail'})
    else :
        #payload는 토큰에 담을 정보를 뜻한다.
        payload={
        'id' : targetId,
        'exp' : datetime.utcnow() + timedelta(seconds=60*60*24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})

    
@app.route('/join/signup', methods=['POST'])
def signup():
   
    #아이디 비밀번호 이메일을 받는다
    targetId = request.form['targetId']
    targetPwd = request.form['targetPwd']
    targetEmail = request.form['targetEmail']

    #받은 비밀번호를 해쉬화 한다.
    pw_hash = hashlib.sha256(targetPwd.encode('utf-8')).hexdigest()

    #DB 안에 저장한다.
    doc = {
            'Id': targetId,
            'Pwd': pw_hash,
            'Email': targetEmail,
        }
    db.users.insert_one(doc)

    return jsonify({'result': 'success'}) 

@app.route('/join/idcheck', methods=['POST'])
def idcheck():
   
    #아이디를 받는다 
    targetId = request.form['targetId']

    #공백이면 취소처리
    if targetId == "" :
        return jsonify({'result': 'black'})
    #해당 아이디의 컬럼이 있는지 확인한다.
    targetUser = db.users.find_one({'Id':targetId})

    print(targetUser)
    if targetUser == None:
        return jsonify({'result': 'success'})
    else :
        return jsonify({'result': 'fail'})   
##########################################################


#학식 메뉴 관련
# @app.route('/mealmenu', methods=['POST'])
# def menuScraping():



#     return menu
##########################################################


# 메인페이지 전체 리스트 관련
@app.route('/api/list', methods=['GET'])
def show_rests():
    sortMode = request.args.get('sortMode', 'like')

    if sortMode == 'like':
        restslist = list(db.junglefood.find({}).sort('like', -1))
    elif sortMode == 'name':
        restslist = list(db.junglefood.find({}).sort('name', 1))
    else:
        return jsonify({'result': 'failure'})

    return jsonify({'result': 'success', 'rest_list': dumps(restslist)})
##########################################################


# 글 작성 상세보기 관련
##########################################################
# @app.route('/contents')
# def contents():
#     return render_template('index.html')

@app.route('/post')
def post():
    return render_template('post.html')

@app.route('/mydetail')
def my_detail():
    return render_template('mydetail.html')

@app.route('/mydetail_modifying')
def modifying_detail():
    return render_template('mydetail_modifying.html')

@app.route('/otherdetail')
def other_detail():
   my_review=db.review.find_one({'user_id': 'test'})
   likes=my_review['like']
   return render_template('otherdetail.html',likes=likes)


# 맛집 리뷰 POST
@app.route('/post/mydetail', methods=['POST'])
def post_my_detail():
   # 1. 클라이언트로부터 데이터를 받기
    restaurant_receive=request.form['restaurant_give']
    category_receive=request.form['category_give']
    comment_receive=request.form['comment_give']
   #  이미지 받기

    # 예외 처리
    if restaurant_receive=="" or comment_receive=="":
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
   #  이미지 받기

    # 예외 처리
    if restaurant_receive=="" or comment_receive=="":
       return jsonify({'result':'empty'})

    # 2. document 만들기 (TEST)
    review = {'restaurant': restaurant_receive, 'category': category_receive, 'comment': comment_receive, 'like':0, 'locate':'kyeongki', 'name':'jungler','rate':5,'user_id':'test', 'favorite':0 }
   # 카테고리와 이미지 추가 필요

    # 3. mongoDB에 데이터 넣기
    db.review.insert_one(review)

    return jsonify({'result':'success'})

@app.route('/like',methods=['POST'])
def like_review():
    # id_receive = request.form['id']
    # review = db.review.find_one({'_id': ObjectId(id_receive)})
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
    
##########################################################

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)