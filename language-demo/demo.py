from lang import Language


if __name__ == '__main__':
    lang_ru = Language('ru')
    lang_en = Language('en')
    print(lang_ru.connection_string)
    print(lang_en.connection_string)
    print(lang_ru.hello)
