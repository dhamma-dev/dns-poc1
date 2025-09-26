from app import create_app

app = create_app()

if __name__ == "__main__":
    # This allows running the app directly for local development
    # without Gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)