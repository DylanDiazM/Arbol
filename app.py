from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div([html.H1("Hello, Render!")])

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host="0.0.0.0", port=port)
