import time
from flask import Flask, Response, render_template_string
from flask import stream_with_context

app = Flask(__name__)

@app.route("/")
def server_1():
    def generate_output():
        age = 0
        template = '<p>{{ name }} is {{ age }} seconds old.</p>'
        context = {'name': 'bob'}
        while True:
            context['age'] = age
            yield render_template_string(template, **context)
            time.sleep(5)
            age += 5

    return Response(stream_with_context(generate_output()))

if __name__ == '__main__':
    app.run(debug=True)