#import ibm_db
from flask import Flask, render_template, request, redirect, url_for, session
import re
from textblob import TextBlob
import requests
import json


app = Flask(__name__)
app.secret_key = 'a'

try:
    conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=98538591-7217-4024-b027-8baa776ffad1.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30875;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=xbz60307;PWD=ks0N68cZYopyf9O2",'','')
    print('Database Connected')
except :
    print('An Error Occured')



@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("index.html")

@app.route('/')
@app.route('/login', methods=["POST", "GET"])
def Login():
    msg=''
    if request.method == 'POST':
        USERNAME = request.form['username']
        PASSWORD = request.form['password']
        sql = "SELECT * FROM SIGNUP WHERE USERNAME = '{}' AND PASSWORD = '{}'".format(USERNAME,PASSWORD)
        stmt = ibm_db.prepare(conn, sql)
        # ibm_db.bind_param(stmt, 1, USERNAME)
        # ibm_db.bind_param(stmt, 2, PASSWORD)
        ibm_db.execute(stmt)
        account = ibm_db. fetch_assoc(stmt)
        print(account)

        if account:
            session['Loggedin'] = True
            session['USERID'] = account['USERID' ]
            session['USERNAME' ] = account[ 'USERNAME' ]
            session['PASSWORD' ] = account['PASSWORD']
            msg = "Logged in successfully!"
            return render_template("index.html",msg=msg)
        else:
            msg = "Incorrect username / Password !"
        return render_template("loginpage.html")
    return render_template("loginpage.html")


@app.route('/register',methods=['GET','POST'])
def Register():
    msg=''
    if request.method=='POST':
        USERNAME = request.form['username']
        EMAIL=request.form['email']
        PASSWORD=request.form['password']
        sql = "SELECT * FROM SIGNUP WHERE USERNAME='{}' AND PASSWORD='{}' ".format(USERNAME,PASSWORD)
        stmt = ibm_db.prepare(conn, sql)
        # ibm_db.bind_param(stmt, 1, USERNAME)
        # ibm_db.bind_param(stmt, 2, PASSWORD)
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)

        print('SQL Select :'+sql)
        if account:
            msg='Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+',USERNAME):
            msg='username must contain only characters and numbers!'
        else:
            sql2='SELECT count(*) FROM SIGNUP'
            stmt2=ibm_db.prepare(conn,sql2)
            ibm_db.execute(stmt2)
            length=ibm_db.fetch_assoc(stmt2)
            print(length)
            insert_sql="INSERT INTO SIGNUP VALUES({},'{}','{}','{}')".format(length['1']+1,USERNAME,EMAIL,PASSWORD)
            prep_stmt=ibm_db.prepare(conn,insert_sql)
            # ibm_db.bind_param(prep_stmt,1,length['1']+1)
            # ibm_db.bind_param(prep_stmt,2,USERNAME)
            # ibm_db.bind_param(prep_stmt,3,EMAIL)
            # ibm_db.bind_param(prep_stmt,4,PASSWORD)
            ibm_db.execute(prep_stmt)
            msg='You have successfully registered!'
            return render_template('loginpage.html',msg=msg)
    return render_template('register.html',msg=msg)

@app.route('/grammar', methods=['POST', 'GET'])
def GrammerCheck():
    if request.method == 'POST':
        text=request.form['text']
        print('Input Text '+text)
        blob=TextBlob(text)
        sentiment = blob.sentiment.polarity
        if sentiment==0.0:
            sentiment='15.020'
        else:
            sentiment
        noun_phrases=blob.noun_phrases
        text_noun_phrases="\n".join(noun_phrases)
        print(text_noun_phrases)
        print(sentiment)
        print(noun_phrases)

        insert_sql="INSERT INTO GRAMMER VALUES ('{}','{}',{},'{}')".format(text,blob,float(sentiment),text_noun_phrases)
        prep_stmt=ibm_db.prepare(conn,insert_sql)
        # ibm_db.bind_param(prep_stmt, 1, text)
        # ibm_db.bind_param(prep_stmt, 2, blob)
        # print('0')
        # ibm_db.bind_param(prep_stmt,3,float(sentiment))
        # print('1')
        # ibm_db.bind_param(prep_stmt,4,noun_phrases)
        # print('2')
        print('Insert Query : '+insert_sql)
        ibm_db.execute(prep_stmt)

        return render_template('Grammercheck.html',sentiment=sentiment,noun_phrases=text_noun_phrases)
    return render_template('Grammercheck.html')

@app.route('/Spell', methods=['POST', 'GET'])
def spelling():
    if request.method == 'POST':
        fieldvalues = request.form['fieldvalues']      
        options = {
        "method": "POST",
        "url": "https://jspell-checker.p.rapidapi.com/check",
        "headers": {
            "content-type": "application/json",
            "X-RapidAPI-Key": "3bd44a43famshc7f15141212c02cp1d4ea3jsnd0daad844b82",
            "X-RapidAPI-Host": "jspell-checker.p.rapidapi.com"
        },
        "data": {
            "language": "enUS",
            "fieldvalues": fieldvalues,
            "config": {
                "forceUpperCase": False,
                "ignoreIrregularCaps": False,
                "ignoreFirstCaps": True,
                "ignoreNumbers": True,
                "ignoreUpper": False,
                "ignoreDouble": False,
                "ignoreWordsWithNumbers": True
            }
        }
    }

        try:
            response = requests.post(options["url"], json=options["data"], headers=options["headers"])
            response_data = response.json()
            print('Response Data :')
            spelling_error_count=response_data['spellingErrorCount']
            print(json.dumps(response_data))
            words=[]
            if spelling_error_count==0:
                return render_template('Spellcheck.html',fieldvalues=fieldvalues,spelling_error_count=spelling_error_count)
            else:
                elements=response_data['elements']
                error_list=[]
                
                for element in elements:
                    error=element['errors'][0]
                    word=error['word']
                    for word in element['errors']:
                        words.append(word['word'])
                    position=error['position']
                    suggestions=' '.join(error['suggestions'])
                    error_list.append((word,position,suggestions))   
            word_res=' '.join(words)
            insert_sql="INSERT INTO SPELLINGCHECKER VALUES ('{}',{},{},'{}')".format(word_res,spelling_error_count,position,suggestions[:5])
            print('Insert SQL :')
            print(insert_sql)
            stmt=ibm_db.prepare(conn,insert_sql)
            ibm_db.execute(stmt)
            
            print(word_res)
            return render_template('Spellcheck.html',word=word_res,spelling_error_count=spelling_error_count)
        except Exception as error:
            print(error)
            return render_template('Spellcheck.html',message='An Error Occured')

    else:
        return render_template('Spellcheck.html')

@app.route('/summarise',methods=['POST','GET'])
def summarise():
    if request.method=='POST':
        text=request.form['text']
        num_sentences=int(request.form['num_sentences'])

        url="https://gpt-summarization.p.rapidapi.com/summarize"

        payload={
            "text":text,
            "num_sentences":num_sentences
        }

        headers={
            "content-type":"application/json",
            "X-RapidAPI-Key":"3bd44a43famshc7f15141212c02cp1d4ea3jsnd0daad844b82",
            "X-RapidAPI-Host":"gpt-summarization.p.rapidapi.com"
        }

        response=requests.post(url,json=payload,headers=headers)
        summary=response.json()
        print('Summary : '+str(summary))
        insert_sql="INSERT INTO SUMMARY VALUES ('{}',{},'{}')".format(text,num_sentences,summary['summary'])
        try:
            stmt=ibm_db.prepare(conn,insert_sql)
            # ibm_db.bind_param(stmt,1,text)
            # ibm_db.bind_param(stmt,2,num_sentences)
            # ibm_db.bind_param(stmt,3,summary)
            print('Insert SQL : '+insert_sql)
            ibm_db.execute(stmt)
            return render_template('Summarise.html',summary=summary['summary'])
        except:
            # if summary['message']:
            #     return render_template('Summarise.html',summary=summary['message'])
            # else:
                return render_template('Summarise.html',message="An Error Occured")
            

    return render_template('Summarise.html')

@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('USERID',None)
    return render_template('loginpage.html') 


if __name__ == '__main__':
 #app.run(host='0.0.0.0"', debug=True)
    app.run()


