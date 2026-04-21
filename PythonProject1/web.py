from flask import Flask, render_template
import db_utils

app = Flask(__name__)
db_utils.init_db()


@app.route("/")
def index():
    leaderboard = db_utils.get_leaderboard(10)
    top_wins = db_utils.get_top_wins(10)
    return render_template("index.html", leaderboard=leaderboard, top_wins=top_wins)


@app.route("/history")
def history():
    rows = db_utils.get_history_rows(50)
    return render_template("history.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)