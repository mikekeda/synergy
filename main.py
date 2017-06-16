from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import text, json
from sanic_jinja2 import SanicJinja2

app = Sanic(__name__)
jinja = SanicJinja2(app)

# Serves files from the static folder to the URL /static
app.static('/static', './static')

@app.route("/")
async def test(request):
    return jinja.render('users.html', request, greetings='Hello!')

@app.route("/courses")
async def test(request):
    return jinja.render('users.html', request, greetings='Hello!')

class UserView(HTTPMethodView):

    def get(self, request, username):
        return text('I am get method' + username)

    def post(self, request, username):
        return text('I am post method')

    def put(self, request, username):
        return text('I am put method')

    def patch(self, request, username):
        return text('I am patch method')

    def delete(self, request, username):
        return text('I am delete method')

app.add_route(UserView.as_view(), '/user/<username>')

app.run(host="0.0.0.0", port=8000, debug=True)

