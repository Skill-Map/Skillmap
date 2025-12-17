from flask import Flask, send_from_directory
import os

# Initialize the Flask application
app = Flask(__name__, static_folder=None)

# Define the root route to serve the index.html file
@app.route('/')
def serve_index():
    """
    Serves the main index.html file from the current directory.
    """
    return send_from_directory('.', 'index.html')

# Define a route to serve any other file (like static assets if needed in the future)
@app.route('/<path:path>')
def serve_static(path):
    """
    Serves other static files from the current directory.
    """
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Get the port number from the environment variable or default to 80
    port = int(os.environ.get('PORT', 80))
    
    # Run the app. 
    # host='0.0.0.0' makes the server accessible from your network.
    # Note: Running on port 80 might require administrator/sudo privileges.
    try:
        print(f"Starting server on http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port)
    except PermissionError:
        print("\n\n----------------------------------------------------")
        print(f"Error: Permission denied to run on port {port}.")
        print("On Linux/macOS, try running with 'sudo python main.py'")
        print("On Windows, try running your terminal as an Administrator.")
        print("----------------------------------------------------\n")
    except OSError as e:
        print(f"\n\nError: Could not start server. {e}\n")
