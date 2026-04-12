# Asteroids
This project is a fork of https://github.com/jucimarjr/asteroids_pygame.
Using Python (3.13):

```pip install -r requirements.txt```

### This project uses pre-commit
For more information on what it does, check [this link](https://pre-commit.com/).
But basically, it cleans up code before committing files.  </br>
How to use:
1. After installing requirements, run `pre-commit install` at least once.
2. It will automatically run before any `git commit`, but can be manually triggered using `pre-commit`.
3. If pre-commit modifies any files, you must `git add` them to staging area.

Note: pre-commit only modifies files on staging area.

## How to Run
Run `python src/main.py`
There is a debug mode for testing stuff, mostly drawing. Run the file with the `--debug` flag:
`python src/main.py --debug`

## New Features
* Shotgun Powerup
* Tough Asteroid

## Credits
Power up original assets by  Eric "ConcernedApe" Barone  
Missing texture by Valve Corporation
