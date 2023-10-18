from flask import Flask
import subprocess
import os
import sys

app = Flask(__name__)

@app.route('/info',methods = ['GET'])
def info():
    result = subprocess.run(["tabix","/data/global.vcf.gz","chr1:3729163-3729163"], stdout=subprocess.PIPE)
    return result.stdout
