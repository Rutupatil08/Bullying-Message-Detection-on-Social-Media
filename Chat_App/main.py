from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahh"
socketio = SocketIO(app)

rooms = {}

model = pickle.load(open("C:/Users/HP/Newproject/Chat_App/static/Dataset/LogisticRegression.pkl", 'rb'))

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code
    
def process_msg(message):
    if message == "hi":
        response = "Welcome!!!"
    else:
        
        my_file = open("C:/Users/HP/Newproject/Chat_App/static/Dataset/stopwords.txt", "r")
        content = my_file.read()
        content_list = content.split("\n")
        my_file.close()

        tfidf_vector = TfidfVectorizer(stop_words = content_list, lowercase = True,vocabulary=pickle.load(open("C:/Users/HP/Newproject/Chat_App/static/Dataset/tfidf_vector_vocabulary.pkl", "rb")))
        vec_data = tfidf_vector.fit_transform([message])
        print(vec_data)
        model = pickle.load(open("C:/Users/HP/Newproject/Chat_App/static/Dataset/LinearSVC.pkl", 'rb'))
        pred = model.predict(vec_data)
        response = str(pred[0])
        print(response)
        
        if(response =='1'):
            response = "Warning!!!!!"
        else:
            response = 'No bullying message found..'
            
    return response

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    response = process_msg(data['data'])
    send(content, to=room)
    rooms[room]["messages"].append(content)
    if response.startswith("Warning!!!!!"):
        warning = {"name": "Warning", "message": "Please be respectful to others in the chat."}
        send(warning, to=request.sid)
        print(f"{session.get('name')} said: {data['data']} (Bullying detected!)")
 
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)

# Time Complexity : O(n + m) 
# Space Complexity: O(n + m)
# where n is the number of stopwords 
# m is the length of the message.