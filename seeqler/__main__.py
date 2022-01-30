import argparse

from .app import Seeqler


def main():
    # Create the parser and add arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('connection_string', nargs='?')

    # Parse and print the results
    args = parser.parse_args()

    app = Seeqler(args.connection_string)
    app.run()


if __name__ == '__main__':
    main()
