import os
import psycopg2
import psycopg2.extras

from flask import Flask, render_template, request, session, redirect, url_for
app = Flask(__name__)
app.secret_key = os.urandom(24).encode('hex')

user = ['', '']

def connectToDb():
    connectionString = 'dbname=stattrack user=tracker password=baseball host=localhost'
    print connectionString
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database")

@app.route('/', methods=['GET','POST'])
def mainIndex():
    
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'
    livechatinfo = {'date': 'January 30th', 'time': '7:00', 'subject': 'College Recruiting'}
    coachAvailable = False
    return render_template('index.html', livechatinfo = livechatinfo, coachAvailable = coachAvailable, user=user, selectedMenu=selectedMenu)
    
@app.route('/about', methods=['GET','POST'])
def showAbout():
    user=['','']
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'

    thecoachoftheweek = "Joe Torre"
    return render_template('about.html', coachoftheweek = thecoachoftheweek, user=user, selectedMenu=selectedMenu)
    
@app.route('/createTeam', methods=['GET','POST'])
def teamCreate():
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'
    conn = connectToDb()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        teamname = request.form['teamname']
        password = request.form['pw']
        insertTeam = "INSERT INTO teams (teamname, password)  VALUES ('%s', crypt(\'%s\', gen_salt('bf')));" % (teamname, password)
        print (insertTeam)
        try:
            cur.execute(insertTeam)
        except:
            print("ERROR inserting into teams")
            print("""INSERT INTO teams (teamname, password)  VALUES ('%s', crypt('%s', gen_salt('bf')));""", (teamname, password) )
            conn.rollback()
    conn.commit()
              
    return render_template('createTeam.html', user=user, selectedMenu=selectedMenu)
    
@app.route('/login', methods=['GET','POST'])
def logIn(): 
    conn = connectToDb()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # if user typed in a post ...
    user = ['','']
    if request.method == 'POST':
        print "HI"
        teamname = request.form['teamname']
        pw = request.form['pw']
        query = "select * from teams WHERE teamname = '%s' AND password = crypt('%s', password)" % (teamname, pw)
        print query
        cur.execute(query)
        if cur.fetchone():
            session['teamName'] = teamname
            session['password'] = pw
            print "Successful login"
            user = [session['teamName'], session['password']]
            print(user)
            return redirect(url_for('mainIndex'))
            
        else:
            print "Unsuccessful login"
    return render_template('login.html', selected='submit', user=user, selectedMenu='loggedOut')
    
@app.route('/myTeam', methods=['GET','POST'])
def teamPage():
    user=['','']
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'

    return render_template('myTeam.html', user=user, selectedMenu=selectedMenu)
    
@app.route('/logout')
def logout():
    session.pop('teamName', None)
    return redirect(url_for('mainIndex'))



# start the server
if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)
