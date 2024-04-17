from flask import Flask

# Create a Flask application
app = Flask(__name__)

# Define a route for the home page
@app.route('/')
def hello():
    return 'Hello, Flask is running!'

# Run the application if this script is executed directly
if __name__ == '__main__':
    print("testprint")
    app.run(debug=True)
