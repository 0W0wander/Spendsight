from backend.app import app

if __name__ == '__main__':
    print("Starting Spendsight...")
    app.run(debug=True, port=5000)
