from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request, redirect
from bson.json_util import dumps
from bson import ObjectId
import json
import jwt
from datetime import datetime,timedelta
import hashlib
import urllib.request
import urllib.error
import time
import requests
import cgi

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle

SECRET_KEY = 'secret_key'

@app.route('/')
def home():
   return render_template('login.html')

@app.route('/join')
def joinpage():
   return render_template('join.html')


@app.route('/mainpage')
def mainapge():
    token_receive = request.cookies.get('mytoken')
    
    rest_list = list(db.review.find({}, {'_id':False}))

    #받은 토큰을 복호화 한 다음 시간이나 증명에 문제가 있다면 예외처리합니다.
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('card.html', rest_list = rest_list, random_rest = json.dumps(rest_list))
    except jwt.ExpiredSignatureError:
        return redirect("http://localhost:5000/")
    except jwt.exceptions.DecodeError:
        return redirect("http://localhost:5000/")

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
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')


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
            'likelist': "",
            'favoritelist' : ""
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
        restslist = list(db.review.find({}).sort('like', -1))
    elif sortMode == 'restaurant':
        restslist = list(db.review.find({}).sort('restaurant', 1))
    else:
        return jsonify({'result': 'failure'})

    return jsonify({'result': 'success', 'rest_list': dumps(restslist)})
##########################################################


# 글 작성 상세보기 관련
##########################################################
# @app.route('/contents')
# def contents():
#     return render_template('index.html')

category={'한식', '중식', '일식', '양식'}

@app.route('/post')
def post():
    cookie_receive = request.cookies.get('myid')
    review2=db.review.find_one({'user_id':cookie_receive})
    print(cookie_receive)
    return render_template('post.html', category=category, review=review2, id = cookie_receive )

@app.route('/mydetail/<idnum>')
def my_detail(idnum):
    idnum_int = int(idnum)
    review2=db.review.find_one({'num':idnum_int})
    return render_template('mydetail.html', review=review2)

@app.route('/mydetail_modifying/<idnum>')
def modifying_detail(idnum):
    idnum_int = int(idnum)
    review2=db.review.find_one({'num':idnum_int})
    return render_template('mydetail_modifying.html',num=idnum, review=review2, category=category)

@app.route('/otherdetail/<idnum>')
def other_detail(idnum):
    idnum_int = int(idnum)
    review=db.review.find_one({'num': idnum_int})
    likes=review['like']
    return render_template('otherdetail.html',likes=likes, review=review)


# 맛집 리뷰 POST
@app.route('/post/mydetail', methods=['POST'])
def post_my_detail():
    #고유 번호 생성
    idnum = db.review.find_one(sort=[("num", -1)])["num"] + 1

   # 1. 클라이언트로부터 데이터를 받기
    restaurant_receive=request.form['restaurant_give']
    category_receive=request.form['category_give']
    comment_receive=request.form['comment_give']
    location_receive=request.form['location_give']
    user_receive=request.form['user_give']
    file = request.files["file_give"]
    
    # static 폴더에 저장될 파일 이름 생성하기
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'
    # 확장자 나누기
    extension = file.filename.split('.')[-1]
    # static 폴더에 저장
    save_to = f'static/{filename}.{extension}'
    file.save(save_to)

    # 예외 처리
    if restaurant_receive=="" or comment_receive=="" or category_receive=="선택하기":
       return jsonify({'result':'empty'})

    # 2. document 만들기
    review = {
        'num' : idnum,
        'restaurant': restaurant_receive,
        'category': category_receive,
        'comment': comment_receive,
        'like':0,
        'locate':location_receive,
        'user_id':user_receive,
        'favorite':0 ,
        'image': f'{filename}.{extension}'
    }
    # 3. mongoDB에 데이터 넣기
    db.review.insert_one(review)

    # print(idnum)
    # print(user_receive)

    return jsonify({'result':'success','idnum':idnum})

@app.route('/modify/mydetail',methods=['POST'])
def modify_my_detail():
    # 1. 클라이언트로부터 데이터를 받기 이미지 받기
    num_receive=request.form['num_give']
    restaurant_receive=request.form['restaurant_give']
    category_receive=request.form['category_give']
    comment_receive=request.form['comment_give']
    location_receive=request.form['location_give']
    file2 = request.files["file_give"]
    # 이미지 받기

    # static 폴더에 저장될 파일 이름 생성하기
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'
    # 확장자 나누기
    extension = file2.filename.split('.')[-1]
    # static 폴더에 저장
    save_to = f'static/{filename}.{extension}'
    file2.save(save_to)

    # 예외 처리1: 빈칸으로 수정할 때
    if restaurant_receive=="" or comment_receive=="" or category_receive=="선택하기":
       return jsonify({'result':'empty'})

    a = int(num_receive)
    # 예외 처리2: 아무것도 수정하지 않았을 때 
    flag = True # 무엇인가 최소 하나 수정한 상태를 전제로
    changed_or_not = db.review.find_one({'num': a})
    if changed_or_not['restaurant']==restaurant_receive and changed_or_not['comment']==comment_receive and changed_or_not['category']==category_receive and changed_or_not['locate']==location_receive:
       flag = False # 아무것도 수정하지 않았다.

    result = db.review.update_one({'num': a},{'$set': {'restaurant': restaurant_receive, 'category':category_receive, 'comment': comment_receive, 'image': f'{filename}.{extension}', 'locate':location_receive}})
    # DB 아이디 쓰는 경우: '_id': ObjectId(id_receive)
    # 이미지 추가 필요
    print(type(num_receive))
    print(result.modified_count)
    print(flag)
    if result.modified_count == 1 and flag: # 수정한 document가 1개이고, 무엇인가 최소 하나 수정한 상태라면 성공
      return jsonify({'result': 'success','idnum': a})
    else: # 수정한 document가 1이 아니거나, 아무것도 수정되지 않은 경우 실패
      return jsonify({'result': 'failure'})

@app.route('/like',methods=['POST'])
def like_review():
    like_num=request.form['like_num']
    id_cookie_receive = request.cookies.get('myid')  
    targetId=db.users.find_one({'Id':id_cookie_receive})

    # 디비의 likelist를 공백 기준으로 소팅하여 like_num 과 같은게 있다면 return failure
    print(type(targetId['likelist']))

    like_str = targetId['likelist'].split()
    print(like_str)

    for i in like_str:
        if i == like_num:
            return jsonify({'result': 'failure'})
    
    idnum_int = int(like_num)
    review2=db.review.find_one({'num':idnum_int})
    new_likes = review2['like'] + 1
    new_likelist = targetId['likelist'] + like_num + " "

    result = db.review.update_one({'num':idnum_int}, {'$set': {'like': new_likes}})
    
    result2 = db.users.update_one({'Id':id_cookie_receive}, {'$set': {'likelist': new_likelist}})

    # 4. 하나의 메모만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success 를 보냄
    if result.modified_count == 1:
       return jsonify({'result': 'success'})
    else:
       return jsonify({'result': 'failure'})

@app.route('/favorite',methods=['POST'])
def favorite_review():
    favorite_num=request.form['favorite_num']
    id_cookie_receive = request.cookies.get('myid')  
    targetUser=db.users.find_one({'Id':id_cookie_receive})

    # 디비의 likelist를 공백 기준으로 소팅하여 like_num 과 같은게 있다면 return failure
    deleted_favoritelist = ""
    favorite_list = targetUser['favoritelist'].split()
    delete_toggle = 0

    # 기존의 즐겨찾기 리스트에 방금 누른 번호가 있다면 빼고 str을 다시 만든다.
    for i in favorite_list:

        if i == favorite_num:
            delete_toggle = 1
            continue
        
        deleted_favoritelist = i + " "

    if delete_toggle == 1:
        db.users.update_one({'Id':id_cookie_receive}, {'$set': {'favoritelist': deleted_favoritelist}})
        return jsonify({'result': 'delete'})
        
    new_favoritelist = targetUser['favoritelist'] + favorite_num + " "

    result = db.users.update_one({'Id':id_cookie_receive}, {'$set': {'favoritelist': new_favoritelist}})
   
    if result.modified_count == 1:
      return jsonify({'result': 'success'})
    else:
      return jsonify({'result': 'failure'})
    
@app.route('/searchfavorite',methods=['POST'])
def search_favorite():
    targetId=request.form['id_cookie_give']
    targetUser=db.users.find_one({'Id':targetId})
    favorite_list = targetUser['favoritelist'].split()

    return jsonify({'result': 'success','favorite_list':favorite_list})

@app.route('/mylist', methods=['GET'])
def my_list():
    myId = request.cookies.get('myid')
    rest_list = list(db.review.find({}, {'_id':False}))
    mylist = []
    for i in range(len(rest_list)):
        if rest_list[i]['user_id'] != myId:
            pass
        else:
            mylist += [rest_list[i]]
    return render_template('mylist.html', mylist=mylist)

@app.route('/mylike', methods=['GET'])
def my_like():
    restslist = list()
    targetId =request.cookies.get('myid')
    targetUser=db.users.find_one({'Id':targetId})
    mylike_list = targetUser['likelist'].split()
    
    for i in mylike_list:
        i_int = int(i)
        mylike = db.review.find_one({'num':i_int})
        print(mylike) 
        restslist.append(mylike)

    return render_template('mylike.html', mylist=restslist)

@app.route('/myfavor', methods=['GET'])
def my_favor():
    restslist = list()
    targetId=request.cookies.get('myid')
    targetUser=db.users.find_one({'Id':targetId})
    myfavor_list = targetUser['favoritelist'].split()
    print(myfavor_list)

    for i in myfavor_list:
        i_int = int(i)
        myfavor = db.review.find_one({'num':i_int}) 
        print(myfavor)
        restslist.append(myfavor)

    return render_template('myfavor.html', mylist=restslist)
    
@app.route('/delete',methods=['POST'])
def delete_review():
    num_receive = request.form['num']
    num_int = int(num_receive)
    # result = db.review.delete_one({'_id': ObjectId(id_receive)})

    result = db.review.delete_one({'num':num_int})
    # 3. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success 를 보냄
    if result.deleted_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})
    
##########################################################

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)