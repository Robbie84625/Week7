from flask import *
import mysql.connector

# 連線到資料庫
con=mysql.connector.connect(
    # 使用者名稱
    user="root",
    # 使用者密碼
    password="123456789",
    # 本機
    host="localhost",
    # 資料庫名稱
    database="message_db",
)

app=Flask(__name__,
        static_folder="public",  # 靜態檔案的資料夾名稱
        static_url_path="/" # 靜態檔案對應的網址路徑
        )


@app.route("/signup",methods=["POST"])
def signup():
    # 從前端接收資料
    name=request.form["name"]
    username=request.form["username"]
    password=request.form["password"]
    
    # 建立Cursor 物件，用來對資料庫下達 SQL 指令
    cursor=con.cursor()
    cursor.execute("SELECT COUNT(*) FROM member WHERE username = %s", (username,))
    username_count = cursor.fetchone()[0]

    if username_count > 0:
        # 如果帳戶已經存在，返回前端錯誤訊息
        return redirect("/error?message=帳戶已經存在")
    else:
        # 新增資料
        cursor.execute("INSERT INTO member(name, username, password) VALUES (%s, %s, %s)", (name, username, password))
        # 執行
        con.commit()

        return """
        <script>
        window.location.href = '/';
        alert('註冊成功');
        </script>
        """
    
    # 關閉資料庫
    cursor.close()



# 設定首頁
@app.route("/")
def home():
    return render_template("home.html")

# 設定會員頁
@app.route("/member")
def member():
    if "name" in session:
        name = session.get("name")
        cursor=con.cursor(dictionary=True)
        cursor.execute("SELECT member.id, member.name, message.content FROM member JOIN message ON member.id = message.member_id ORDER BY message.time;")
    
        messageContent = cursor.fetchall()
        

        # 關閉資料庫
        cursor.close()
        return render_template("Member.html", name=name, messages=messageContent)
    else:
        return redirect("/")

#設定登入失敗
@app.route("/error")
def error():
    msg=request.args.get("message","發生錯誤，請聯繫客服")
    return render_template("error.html",message=msg)

# 設定登入方法
@app.route("/signin",methods=["POST"])
def signin():
    # 從前端接收資料
    username=request.form["username"]
    password=request.form["password"]

    # 建立Cursor 物件，用來對資料庫下達 SQL 指令
    cursor=con.cursor()
    
    cursor.execute("SELECT * FROM member WHERE username = %s AND password = %s" , (username,password))
    user_data = cursor.fetchone()
    # 檢查帳號是否存在並且密碼是否正確
    if user_data==None:
        return redirect("/error?message=帳號或密碼輸入錯誤")

    else:    
        session["name"] =  user_data[1]
        session["id"] =  user_data[0]
        return redirect("/member")
        
    # 關閉資料庫
    cursor.close()

@app.route("/signout")
def signout():
    if "name" in session or "id" in session: 
        del session["name"]
        del session["id"]
        return redirect("/")
    return redirect("/")

@app.route("/createMessage",methods=["POST"])
def createMessage():
    # 從前端接收資料
    content=request.form["messageContent"]
    userId = session["id"]

    # 建立Cursor 物件，用來對資料庫下達 SQL 指令
    cursor=con.cursor()
    
    cursor.execute("INSERT INTO message(member_id, content) VALUES (%s, %s)", (userId, content))
    # 執行
    con.commit()
    return redirect("/member")

@app.route('/api/member', methods=['GET', 'PATCH'])
def get_data():
    if request.method == 'GET':
        username = request.args.get('username')
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT id, name,username FROM member WHERE username=%s",(username,))
        data = cursor.fetchall()
        if ("name" in session or "id" in session) and data:
            response_data = {"data": data[0]}
        else:
            response_data = {"data": None}
        return jsonify(response_data)
    
    if request.method == 'PATCH':
        data = request.get_json()  # 從請求中取得傳送的JSON資料
        newName = data.get('name')

        if newName is not None and "name" in session:
            username = request.args.get('username')
            cursor = con.cursor()

            username=session['name']
            # 更新資料庫中的名稱
            cursor.execute("UPDATE member SET name=%s WHERE name=%s", (newName, session['name']))
            con.commit()

            session['name'] = newName
            return jsonify({"ok":True})

        else:
            return jsonify({"error":True})
    
    cursor.close()



app.secret_key="a123456789" # 設定session密鑰

app.run(port=3000)