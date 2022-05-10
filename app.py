from flask import Flask, render_template, request, session
import requests
import os

END_URL = "https://word-guessing-game.onrender.com/"

app = Flask(__name__)
app.secret_key = os.urandom(12)


@app.route('/')
def home():
    return render_template('index.jinja2')


@app.route('/new_game')
def new_game():
    try:
        game = requests.post(END_URL)
        game.raise_for_status()
        gameinfo = game.json()
        session['gameid'] = gameinfo['game']['id']
        return render_template('new_game.jinja2', game_info=gameinfo, is_new_game=1)
    except requests.exceptions.HTTPError as err:
        err_str = "Http Error"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.ConnectionError as err:
        err_str = "Error Connecting"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.Timeout as err:
        err_str = "Timeout Error"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.RequestException as err:
        err_str = "OOps: Something Else"
        return render_template('index.jinja2', err_str=err_str)


def validate(guessed_letter):
    guessed_letter = guessed_letter.strip()
    if guessed_letter.isalpha() & len(guessed_letter) == 1:
        return guessed_letter
    else:
        err_str = "Invalid Input. Try another"
        return err_str


@app.route('/guess_letter')
def guess_letter():
    guessed_letter = validate(request.args.get('guessed_letter'))
    game_id = session.get('gameid', None)
    # get current state of the game
    try:
        gameState = requests.get(END_URL + game_id)
        gameState.raise_for_status()
        gameStateData = gameState.json()
    except requests.exceptions.BaseHTTPError as err:
        err_str = "HTTP Error. Try again!"
        return render_template('index.jinja2', err_str=err_str)

    # If Invalid input render game page with error message
    if len(guessed_letter) != 1:
        return render_template('new_game.jinja2', is_new_game=0, game_info=gameStateData, err_str=guessed_letter)
    else:
        # Input is Valid, check if it exists in already guessed list
        if guessed_letter in gameStateData['game']['guesses']:
            err_str = "Already guessed this letter. Try another one"
            print(guessed_letter, err_str)
            return render_template('new_game.jinja2', is_new_game=0,
                                   game_info=gameStateData, err_str=err_str)

    url = END_URL + game_id + "/" + guessed_letter

    try:
        response = requests.put(url)
        response.raise_for_status()

        if response.status_code == 200:
            gameinfo = response.json()
            if "lost" in gameinfo:
                return render_template('result.jinja2', game_info=gameinfo, won=0)
            if "won" in gameinfo:
                return render_template('result.jinja2', game_info=gameinfo, won=1)
            if "error" in gameinfo:
                return gameinfo['error']
            return render_template('new_game.jinja2', game_info=gameinfo, is_new_game=0)

    except requests.exceptions.HTTPError as err:
        err_str = "Http Error"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.ConnectionError as err:
        err_str = "Error Connecting"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.Timeout as err:
        err_str = "Timeout Error"
        return render_template('index.jinja2', err_str=err_str)
    except requests.exceptions.RequestException as err:
        err_str = "OOps: Something Else"
        return render_template('index.jinja2', err_str=err_str)


if __name__ == '__main__':
    app.run(debug=True)
