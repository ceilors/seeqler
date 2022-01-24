import sys

from .app import Seeqler


def main():
    app = Seeqler(sys.argv[1])
    app.run()


if __name__ == '__main__':
    main()
