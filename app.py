from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_session import Session
import stripe

import mysql.connector
from tokenreset import token
from Atokenreset import token
from otp import genotp
from cmail import sendmail
import mysql.connector
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import random
from io import BytesIO 
import os 
stripe.api_key='sk_test_51N0lsySHG8cb6YjgXXX0qmJosgB7Zmwvok6hA6yC3rcTJ4j4jCsrFnuZWRoBEjJ2getr4R577lBf3JncFcH9TYVp00PACq7qkd'                    
app=Flask(__name__)
app.secret_key='67@hjyjhk'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='project'
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
with mysql.connector.connect(host=host,user=user,password=password,db=db,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute('create table if not exists restaurant(rid int primary key,rname varchar(15),rplace varchar(20),password varchar(10),email varchar(35))')
    cursor.execute('create table if not exists users(uname char(15) primary key,mobile bigint unique,Gender varchar(6),email varchar(35), password char(10))')
    cursor.execute('create table if not exists additems(itemid varchar(9) primary key,itemname varchar(30),price int,category enum('South India','North India','Chinese','French') rid int,foreign key(rid) references(restaurant))')
    cursor.execute('create table if not exists orders(orderid int primary key auto_increment,itemid varchar(9),itemname varchar(30),qty int ,total_price int ,uname char(15),foreign key(uname) references users(uname))')
    cursor.execute('create table if not exists contactus(Name varchar(20),mobile bigint,email varchar(30),address varchar(40))')
mysql=MySQL(app)
Session(app)
@app.route('/')
def index():
    cursor=mysql.connection.cursor()
    cursor.execute('select rid,rname from restaurant')
    restaurant=cursor.fetchall()
    print(restaurant)
    return render_template('home2.html',restaurant=restaurant)
@app.route('/register',methods=['GET','POST'])
def uregister():
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form['mobile']
        Gender=request.form['Gender']
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into users(uname,mobile,Gender,email,password) values(%s,%s,%s,%s,%s)',[name,mobile,Gender,email,password])
       # cursor.execute('Select uname from users')
        data=cursor.fetchall()
        cursor.close()
        otp=genotp()
        subject='Thanks for registering to the application'
        body=f'Use this otp to register {otp}'
        sendmail(email,body,subject)
        return render_template('otp.html',otp=otp,name=name,mobile=mobile,Gender=Gender,email=email,password=password)
    else:
        flash('Invalid Details')
        return render_template('usersignin.html')
    return render_template('usersignin.html')
@app.route('/login',methods=['GET','POST'])
def ulogin():
    if session.get('user'):
        return redirect(url_for('index'))
    if request.method=='POST':
        uname=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from users where uname=%s and password=%s',[uname,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid uname or password')
            return render_template('userlogin.html')
        else:
            session['user']=uname
            if not session.get(session.get('user')):
                session[session.get('user')]={}
            return redirect(url_for('index'))
    return render_template('userLogin.html')
@app.route('/logout')
def logout():
     if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
     else:
        flash('u are already logged out!')
        return redirect(url_for('ulogin'))
@app.route('/alogout')
def Alogout():
    if session.get('admin'):
        session.pop('admin')
        return redirect(url_for('index'))
    else:
        flash('u are already logged out!')
        return redirect(url_for('Alogin'))
        #return redirect(url_for('loginp'))

@app.route('/otp/<otp>/<name>/<mobile>/<Gender>/<email>/<password>',methods=['GET','POST'])
def otp(otp,name,mobile,Gender,email,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            lst=[name,mobile,Gender,email,password]
            query='insert into users values(%s,%s,%s,%s,%s)'
            cursor=mysql.connection.cursor()
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('ulogin'))
        else:
            flash('Wrong otp')
    return render_template('otp.html',otp=otp,name=name,mobile=mobile,Gender=Gender,email=email,password=password)
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        name=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select uname from users')
        data=cursor.fetchall()
        print(data)
        if (name,) in data:
            cursor.execute('select email from users where uname=%s',[name])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using:- {request.host+url_for("createpassword",token=token(name,360))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('ulogin'))
        else:
            return 'Invalid uname'
    return render_template('forgot.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        name=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['New-Password']
            cpass=request.form['conform-password']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where uname=%s',[npass,name])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('forgotpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'
@app.route('/adminregister',methods=['GET','post'])
def Aregister():
    if request.method=='POST':
        rid=request.form['rid']
        rname = request.form['rname']
        rplace= request.form['rplace']
        password=request.form['password']
        email = request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute ('select rid from restaurant')
        data = cursor.fetchall()
        cursor.execute ('select email from restaurant')
        edata = cursor.fetchall()
        cursor.close()
        otp = genotp() 
        subject='thanks for registering'
        body = f'use this otp register {otp}'
        sendmail(email,subject,body)
        return render_template('Aotp.html',otp=otp,rid=rid,rname=rname,rplace=rplace,password=password,email=email)
    else:
        flash('Invalid Details')
        return render_template('adminregister.html')
    return render_template('adminregister.html')
@app.route('/Aotp/<otp>/<rid>/<rname>/<rplace>/<password>/<email>',methods=['GET','POST'])
def Aotp(otp,rid,rname,rplace,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            cursor.execute('insert into restaurant values(%s,%s,%s,%s,%s)',[rid,rname,rplace,password,email])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('Alogin'))
        else:
            flash('Wrong otp')
    return render_template('Aotp.html',otp=otp,rid=rid,rname=rname,rplace=rplace,password=password,email=email)
@app.route('/adminlogin',methods=['GET','POST'])
def Alogin():
    if request.method=='POST':
        rid=request.form['rid']
        password=request.form['Password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from restaurant where rid=%s and password=%s',[rid,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid rid or password')
            return render_template('adminlogin.html')
        else:
            session['admin']=rid
            return render_template('adminstatus.html')
    return render_template('adminlogin.html')
@app.route('/aforgetpassword',methods=['GET','POST'])
def Aforget():#after clicking the forget password
    if request.method=='POST':
        userid=request.form['rid']
        cursor=mysql.connection.cursor()
        cursor.execute('select rid from restaurant')# fetch the username data in the table students
        data=cursor.fetchall()#fetching all the rollno data and store it in the "data" variable 
        if (userid,) in data:# if the given rollno of the user is present in tha database->data
            cursor.execute('select email from restaurant where rid=%s',[userid])#it fetches email related to the rollno 
            data=cursor.fetchone()[0]#fetch the only one email related to the rollno 
            #print(data)
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("acreatepassword",token=token(userid,200))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            #return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('Aforgot.html')
@app.route('/acreatepassword/<token>',methods=['GET','POST'])
def Acreatepassword(token):#to create noe password and conform the password
        try:
            s=Serializer(app.config['SECRET_KEY'])
            userid=s.loads(token)['admin']
            if request.method=='POST':
                npass=request.form['new-password']
                cpass=request.form['confirm-password']
                if npass==cpass:
                    cursor=mysql.connection.cursor()
                    cursor.execute('update restaurant set password=%s where rid=%s',[npass,username])
                    mysql.connection.commit()
                    return 'Password reset Successfull'
                    return redirect(url_for('Alogin'))
                else:
                    return 'Password mismatch'
            return render_template('Adminforgotpassword.html')
        except Exception as e:
            print(e)
            return 'Link expired try again'
@app.route('/adminstatus')
def adminstatus():
    if session.get('admin'):
        return render_template('adminstatus.html')
    else:
        return redirect(url_for('Alogin'))

@app.route('/admindashboard',methods=['GET','POST'])
def admindashboard():
    if request.method=="POST":
        id1=genotp()
        itemname=request.form['itemname']
        price=request.form['price']
        category=request.form['category']
       
        image=request.files['image']
        cursor=mysql.connection.cursor()
        filename=id1+'.jpg'
        cursor.execute('insert into additems(itemid,itemname,price,category,rid) values(%s,%s,%s,%s,%s)',[id1,itemname,price,category,session.get('admin')])
        mysql.connection.commit()
        print(filename)
        path=r"C:\Users\91901\Desktop\masthanbee.project\static"
        image.save(os.path.join(path,filename))
        print('success')
        return redirect(url_for('adminstatus'))
    return render_template('admindashboard.html')
@app.route('/available', methods=['GET', 'POST'])
def availableitems():
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from additems where rid=%s',[session.get('admin')])
        items=cursor.fetchall()
        return render_template('Availableitems.html',items=items)
    else:
        return render_template('adminlogin.html')
@app.route('/updateitem/<itemid>',methods=['GET','POST'])
def updateitem(itemid):
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select itemname,category,price from additems where itemid=%s',[itemid])
        items=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            Itemname=request.form['name']
            category=request.form['category']
            price=request.form['price']
            cursor=mysql.connection.cursor()
            cursor.execute('update additems set Itemname=%s,category=%s,price=%s where itemid=%s',[Itemname,category,price,itemid])
            mysql.connection.commit()
            cursor.close()
            flash('item updated successfully')
            return redirect(url_for('availableitems'))
        return render_template('update.html',items=items)
    else:
        return redirect(url_for('alogin'))
@app.route('/deleteitem/<itemid>')
def deleteitem(itemid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mysql.connection.commit()
    cursor.close()
    path=r"C:\Users\91901\Desktop\masthanbee.project\static"
    filename=f"{itemid}.jpg"
    os.remove(os.path.join(path,filename))
    flash('item deleted successfully')
    return redirect(url_for('availableitems'))
@app.route('/itemspage')
def itemspage():
    cursor=mysql.connection.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    return render_template('itemspage.html',items=items)
@app.route('/homepage/<category>')
def homepage(category):
    cursor=mysql.connection.cursor()
    cursor.execute('select * from additems where category=%s',[category])
    items=cursor.fetchall()
    print(items)
    return render_template('itemspage.html',items=items)
@app.route('/returantshome/<name>')
def resturantshome(name):
    cursor=mysql.connection.cursor()
    cursor.execute('select rname from restaurant')
    resturants=cursor.fetchall()
    
    cursor.execute('select rid from restaurant where rname=%s',[name])
    rid=cursor.fetchone()[0]
    cursor.execute('select * from additems where rid=%s',[rid])
    ritems=cursor.fetchall()
    
    return render_template('restauranthome.html',ritems=ritems,resturants=resturants)
#--------------------------------cart card---------------------------------------------------
@app.route('/items',methods=['GET','POST'])
def items():
    return render_template('itemsPage.html')
@app.route('/cart/<itemid>/<name>/<price>')
def cart(itemid,name,price):
    if not session.get('user'):#--noor
        return redirect(url_for('ulogin'))#--noor
    if itemid not in session.get(session.get('user')):
        session[session.get('user')][itemid]=[name,1,price]
        session.modified=True
        print(session[session.get('user')])
        flash(f'{name} added to cart')
        return redirect(url_for('viewcart'))
    session[session.get('user')][itemid][1]+=1
    flash('Item already in cart quantity increased to +1')
    return redirect(url_for('viewcart'))
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))#---noor
    items=session.get(session.get('user')) if session.get(session.get('user')) else 'empty'
    if items=='empty':
        return 'no products in cart'
    #print(items)
    return render_template('cart.html',items=items)
@app.route('/remcart/<item>')
def rem(item):
    if session.get('user'):
        session[session.get('user')].pop(item)
        return redirect(url_for('viewcart'))
    return redirect(url_for('login'))
@app.route('/pay/<itemid>/<name>/<int:price>',methods=['POST'])
def pay(itemid,price,name):
    if session.get('user'):
        q=int(request.form['qty'])
        username=session.get('user')
        total=price*q
        checkout_session=stripe.checkout.Session.create(
            success_url=url_for('success',itemid=itemid,itemname=name,q=q,total=total,_external=True),
            line_items=[
                {
                    'price_data': {
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price*100,
                        'currency': 'inr',
                    },
                    'quantity': q,
                },
                ],
            mode="payment",)
        return redirect(checkout_session.url)
    else:
        return redirect(url_for('login'))
@app.route('/success/<itemid>/<itemname>/<q>/<total>')
def success(itemid,itemname,q,total):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('insert into orders(itemid,itemname,qty,total_price,uname) values(%s,%s,%s,%s,%s)',[itemid,itemname,q,total,session.get('user')])
        mysql.connection.commit()
        
        return 'Order Placed'
    return redirect(url_for('login'))
@app.route('/orders')
def orders():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from orders where uname=%s',(session.get('user'),))
       
        orders=cursor.fetchall()
        
        return render_template('orders.html',orders=orders)
@app.route('/search',methods=['GET','POST'])
def search():
    
    if request.method=="POST":
        name=request.form['search']
        cursor=mysql.connection.cursor()
        cursor.execute('select * from additems where Itemname=%s',[name])
        data=cursor.fetchall()
        return render_template('itemspage.html',items=data)
            
         
    
if __name__=='__main__':
    app.run(debug=True,use_reloader=True)
