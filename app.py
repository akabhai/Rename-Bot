from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Renamer Bot is Online (Checking TBC for Access)'

if __name__ == "__main__":
    app.run()
