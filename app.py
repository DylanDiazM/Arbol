from dash import Dash, html

# Define the Dash application
app = Dash(__name__)

# Set the layout
app.layout = html.Div([
    html.H1("Hello, Render!")
])

# Ensure compatibility with Render's environment
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))  # Render uses the PORT environment variable
    app.run_server(debug=False, host="0.0.0.0", port=port)
