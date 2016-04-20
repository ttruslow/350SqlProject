import os
import sys
import uuid
import psycopg2
import psycopg2.extras

from flask import Flask, render_template, request, session, redirect, url_for
from flask.ext.socketio import SocketIO, emit
app = Flask(__name__)

#app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.urandom(24).encode('hex')
socketio = SocketIO(app)
user = ['', '']
users = {}
messages = []

def connectToDb():
    connectionString = 'dbname=stattrack user=tracker password=baseball host=localhost'
    print connectionString
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database")
        
@socketio.on('connect', namespace='/statTrack')
def makeConnection():
    conn = connectToDb()
    cur = conn.cursor()
    print ('connected')
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'
    
    query = "select * from messages;"
    try:
        cur.execute(query)
    except:
        print("could not retrieve existing messages")
    messages = cur.fetchall()
    print(messages)
    
    for message in messages:
        print(message)
        msg = {"text": message[2], "name": message[1]}
        emit('message', msg)

@socketio.on('message', namespace='/statTrack')
def new_message(message):
    conn = connectToDb()
    cur = conn.cursor()
    tmp = {'text': message, 'name': session['teamName']}
    print(tmp)
    messages.append(tmp)
    try:
        cur.execute("INSERT INTO messages (author, message) VALUES (%s, %s);", (session['teamName'], message))
    except:
        print("Error adding to db")
        print(" Tried: INSERT INTO messages (author, message) VALUES (%s, %s);", (session['teamName'], message))
        conn.rollback()
    conn.commit()
    print("TEST IN MESSAGE")
    emit('message', tmp, broadcast=True)
    
@socketio.on('identify', namespace='/statTrack')
def on_identify(message):
    print('identify ' + message)
    users[session['teamName']] = {'username': message}

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
    livechatinfo = {'date': 'March 15th', 'time': '7:00', 'subject': 'StatTrack\'s newest features'}
    coachAvailable = True
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
    printError = 'no'
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
    error = 'no'
    teamexists = 'no'
    if request.method == 'POST':
        teamname = request.form['teamname']
        password = request.form['pw']
        password2 = request.form['pw2']
        cur.execute("select * from teams where teamname = %s;", (teamname,))
        if cur.fetchone():
            teamexists = 'yes'
            error = 'yes'
        else:
            if password == password2:
                insertTeam = "INSERT INTO teams (teamname, password)  VALUES (%s, crypt(%s, gen_salt('bf')));", (teamname, password)
                print (insertTeam)
                try:
                    cur.execute("INSERT INTO teams (teamname, password)  VALUES (%s, crypt(%s, gen_salt('bf')));", (teamname, password))
                except:
                    error = 'yes'
                    print("ERROR inserting into teams")
                    print("INSERT INTO teams (teamname, password)  VALUES (%s, crypt(%s, gen_salt('bf')));", (teamname, password) )
                    conn.rollback()
                    
                conn.commit()        
            else:
                printError = 'yes'
                error = 'yes'
        if error == 'no':
            return redirect(url_for('logIn'))
    
              
    return render_template('createTeam.html', user=user, selectedMenu=selectedMenu, printError=printError, teamexists=teamexists)
    
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
            return redirect(url_for('teamPage'))
            
        else:
            print "Unsuccessful login"
    return render_template('login.html', selected='submit', user=user, selectedMenu='loggedOut')
    
@app.route('/myTeam', methods=['GET','POST'])
def teamPage():
    conn = connectToDb()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    user=['','']
    if 'teamName' in session:
        print("INDEX: IN SESSION")
        user = [session['teamName'], session['password']]
        selectedMenu = 'loggedIn'
        team = session['teamName']  
    else:
        user = ['Not Logged In','']
        print("INDEX: NOT IN SESSION")
        selectedMenu = 'loggedOut'
        team = ''
      
    if request.method == 'POST':
        print("Request method is POST")
        if request.form['submit'] == 'Add Player':
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            position = request.form['position']
            number = request.form['number']
            team = session['teamName']
            print("Player info: %s %s %s %s %s", (firstname, lastname, position, number, team))
            try:
                cur.execute("insert into players (lastname, firstname, position, number, team) VALUES (%s, %s, %s, %s, %s);", (lastname, firstname, position, number, team))
            except:
                    print("ERROR inserting into players")
                    print ("TRIED: insert into players (lastname, firstname, position, number, team) VALUES (%s, %s, %s, %s, %s);", (lastname, firstname, position, number, team))
                    conn.rollback()
            conn.commit()
        if request.form['submit'] == 'Submit Result':
            playerchosen = request.form['player']
            rbis = request.form['rbi']
            result = request.form['stat']
            print("playerchosen: %s", (playerchosen,))
            if result == 'single':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set singles = singles + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set rbi = rbi + %s where playerid = %s;", (rbis, playerchosen))
            if result == 'double':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set doubles = doubles + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set rbi = rbi + %s where playerid = %s;", (rbis, playerchosen))
            if result == 'triple':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set triples = triples + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set rbi = rbi + %s where playerid = %s;", (rbis, playerchosen))
            if result == 'homerun':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set homeruns = homeruns + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set runs = runs + 1 where playerid = %s;", (playerchosen,))
                if rbis == '0':
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
                else:
                    cur.execute("update players set rbi = rbi + %s where playerid = %s;", (rbis, playerchosen))
            if result == 'walk':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set walks = walks + 1 where playerid = %s;", (playerchosen,))
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'hitbypitch':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hitbypitch = hitbypitch + 1 where playerid = %s;", (playerchosen,))
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'flyout':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set flyouts = flyouts + 1 where playerid = %s;", (playerchosen,))
            if result == 'groundout':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set groundouts = groundouts + 1 where playerid = %s;", (playerchosen,))
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'onbyerror':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set onbyerror = onbyerror + 1 where playerid = %s;", (playerchosen,))
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'strikeout':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab + 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set strikeouts = strikeouts + 1 where playerid = %s;", (playerchosen,))
            if result == 'sacbunt':
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'sacfly':
                cur.execute("update players set pa = pa + 1 where playerid = %s;", (playerchosen,))
                if rbis == 1:
                    cur.execute("update players set rbi = rbi + 1 where playerid = %s;", (playerchosen,))
            if result == 'stolenbase':
                cur.execute("update players set stolenbases = stolenbases + 1 where playerid = %s;", (playerchosen,))
            if result == 'runscored':
                cur.execute("update players set runs = runs + 1 where playerid = %s;", (playerchosen,))
                
        if request.form['submit'] == '-1 Single':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select singles from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set singles = singles - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Double':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select doubles from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set doubles = doubles - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Triple':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select triples from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set triples = triples - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Homerun':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select homeruns from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set hits = hits - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set homeruns = homeruns - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Base on Balls':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select walks from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set walks = walks - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Strikeout':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select strikeouts from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set strikeouts = strikeouts - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Run':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select runs from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set runs = runs - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 SB':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select stolenbases from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set stolenbases = stolenbases - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 On by Error':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select onbyerror from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set onbyerror = onbyerror - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Groundout':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select groundouts from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set groundouts = groundouts - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Flyout':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select flyouts from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set ab = ab - 1 where playerid = %s;", (playerchosen,))
                cur.execute("update players set flyouts = flyouts - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Sac Fly':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select pa from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
            
        if request.form['submit'] == '-1 Sac Bunt':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            
        if request.form['submit'] == '-1 Hit By Pitch':
            playerchosen = request.form['player']
            print("playerchosen: %s", (playerchosen,))
            cur.execute("select pa from players where playerid = %s;", (playerchosen,))
            temp = cur.fetchone()
            print("Temp: %s", (temp,))
            if temp[0] > 0:
                cur.execute("update players set pa = pa - 1 where playerid = %s;", (playerchosen,))
        
    else:
        print("Request method is GET")
    
    
    #cur.execute("select firstname, lastname, number, position, playerid, hits, doubles, triples, homeruns, rbi, walks, runs, stolenbases, ab, strikeouts, hitbypitch, onbyerror, pa from players where team = %s;", (team,))
    
    
    conn.commit()
    cur.execute("select players.firstname, players.lastname, players.number, players.position, players.playerid, players.hits, players.doubles, players.triples, players.homeruns, players.rbi, players.walks, players.runs, players.stolenbases, players.ab, players.strikeouts, players.hitbypitch, players.onbyerror, players.pa, teams.teamname from players JOIN teams on players.team = teams.teamname AND players.team = %s;", (team,))
    playerList = cur.fetchall();
        
    return render_template('myTeam.html', user=user, selectedMenu=selectedMenu, playerList = playerList)
    
@app.route('/logout')
def logout():
    session.pop('teamName', None)
    return redirect(url_for('mainIndex'))

# start the server
if __name__ == '__main__':
    #app.run(host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)
        
