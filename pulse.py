#!/usr/bin/env python

from flask import Flask
from flask import render_template

# Initialize app.
app = Flask(__name__)
app.debug = True

# Routes.

@app.route("/")
def index():
	return render_template("index.html")



# Boot it up.

if __name__ == "__main__":
    app.run()
