from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        if request.form: # able to parse the POST as JSON
            print(request.form)
        else: # unable to parse the POST
            print(request.data)