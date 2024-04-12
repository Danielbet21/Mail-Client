from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
import gmail

app = Flask(__name__)
app.secret_key = "secret"
app.permanent_session_lifetime = timedelta(days=1)

"""
 Home
 Aim:		Display the home page
"""
@app.route("/")
def home():
    return render_template("GmailHome.html")

"""
 Login
 Aim:		Check if the user is logged in ,else redirect to login page  
 Output:	User Page & info / login
"""
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # retrieving data and set TTL for the user data
        session.permanent = True
        username = request.form["nm"]
        session["user"] = username
        flash("Logged in successfully!", "info")
        return redirect(url_for("user"))
    else:
        if user in session:
            flash("Already logged in", "info")
            return render_template("user.html")

        return render_template("login.html")


"""
 User
 Aim:		Display the user his page
"""
@app.route("/user")
def user():
    if "user" in session:
        usr = session["user"]
        return render_template("user.html", name=usr)
    else:
        usr = session["user"]
        return redirect(url_for("login"))


"""
 Logout
 Aim:		Dispaly the logout page  
"""
@app.route("/logout")
def logout():
    if "user" in session:
        usr = session["user"]
        flash(f"You have been logged out {usr}!", "info")
    session.pop("user", None)
    return redirect(url_for("login"))




if __name__ == "__main__":
    app.run(debug=True)