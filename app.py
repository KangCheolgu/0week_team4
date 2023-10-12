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

@app.route('/mealmenu', methods=['POST'])
def menuScraping():



    return menu
  

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



if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)