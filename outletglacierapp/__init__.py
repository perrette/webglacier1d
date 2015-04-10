from flask import Flask

app = Flask(__name__)
app.secret_key = 's3cr3t'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # json responses not pretty pretty printed

import outletglacierapp.views
