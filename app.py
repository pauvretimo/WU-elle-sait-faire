from os import urandom
import os
from waitress import serve
from flask import Flask, render_template

##
FLAG = "CATF{lfsr_0r_N0t_LFSR}"

class LFSR:

    def __init__(self, i):
        self.seed = self.gen_seed(i)
        self.state = self.seed

    def gen_seed(self, i):
        while i == None or i == 0:
            i = urandom(2)[0]
        seed = [int(x) for x in bin(i)[2:]]
        while len(seed) < 9:
            seed += [0]
        return seed[:9]

    def next(self):
        self.state = [(self.state[0] + self.state[5] + self.state[7] + self.state[8]) % 2] + self.state[:-1]


class getFlag:

    def __init__(self, FLAG):
        self.flag = FLAG.encode()

    def encrypt(self):
        l = LFSR(None)
        for k in range(urandom(1)[0]):
            l.next()

        encrypted_flag = b""
        for k in range(len(self.flag)):
            n = (-1)**l.state[0]
            key = ((n*sum([(2*l.state[x+1])**x for x in range(len(l.state[1:]))]))%255)
            encrypted_flag += (self.flag[k] ^ key).to_bytes(1, 'big')
            for i in range(urandom(1)[0]):
                l.next()
        return encrypted_flag


##




app = Flask(__name__)

@app.route("/")
def chall():
    return render_template("app.html")

@app.route("/flag")
def sendFlag():
    f = getFlag(FLAG)
    return  '''
<style>
html {
    background-color: rgb(10,10,10);
}
p {
    color:white;
}
</style>
<p>''' + str(f.encrypt().hex()) + '</p>'

@app.errorhandler(404)
def page_not_found(error):
    return "not found"

if __name__ == '__main__':

    print("Launching the server ...")
    serve(app, host='0.0.0.0', port=str(os.getenv('SERVER_PORT', 80)), _quiet=False)
