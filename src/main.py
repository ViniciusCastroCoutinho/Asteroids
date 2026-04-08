# ASTEROIDE SINGLEPLAYER v1.0
# This file starts the application and launches the main game loop.

from game import Game
from debug import GameDebug
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()


def main():
    # Start the game instance and run the main loop. If --debug flag is passed, runs the game in debug mode
    if args.debug:
        GameDebug().run()
    else:
        Game().run()


if __name__ == "__main__":
    main()
