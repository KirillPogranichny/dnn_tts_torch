"""Data loader for the LJSpeech dataset. See: https://keithito.com/LJ-Speech-Dataset/"""
import os
import re
import codecs
import unicodedata
import numpy as np

from torch.utils.data import Dataset

vocab = "PE abcdefghijklmnopqrstuvwxyz'.?"  # P: Padding, E: EOS.
char2idx = {char: idx for idx, char in enumerate(vocab)}
idx2char = {idx: char for idx, char in enumerate(vocab)}


# Производим нормализацию алфавита с помощью декомпозиции NFD https://habr.com/ru/articles/45489/
# NFD раскладывает сложные символы вроде "é" на "e" и символ с акутом
''' 'Lu': Letter, Uppercase (Заглавная буква)
    'Ll': Letter, Lowercase (Строчная буква)
    'Lt': Letter, Titlecase (Заглавная буква в начале слова)
    'Lm': Letter, Modifier (Модификатор буквы)
    'Lo': Letter, Other (Другая буква)
    'Mn': Mark, Non-Spacing (Неразрывный знак)
    'Mc': Mark, Spacing Combining (Разрывный знак)
    'Me': Mark, Enclosing (Окружающий знак)
    'Nd': Number, Decimal Digit (Десятичная цифра)
    'Nl': Number, Letter (Буквенная цифра)
    'No': Number, Other (Другое число)
    'Pc': Punctuation, Connector (Соединительный знак)
    'Pd': Punctuation, Dash (Тире)
    'Ps': Punctuation, Open (Открывающий знак)
    'Pe': Punctuation, Close (Закрывающий знак)
    'Pi': Punctuation, Initial Quote (Начальный кавычки)
    'Pf': Punctuation, Final Quote (Конечный кавычки)
    'Po': Punctuation, Other (Другой знак препинания)
    'Sm': Symbol, Math (Математический символ)
    'Sc': Symbol, Currency (Валютный символ)
    'Sk': Symbol, Modifier (Модификаторный символ)
    'So': Symbol, Other (Другой символ)
    'Zs': Separator, Space (Пробел)
    'Zl': Separator, Line (Линия переноса)
    'Zp': Separator, Paragraph (Параграф)
    'Cc': Other, Control (Управляющий символ)
    'Cf': Other, Format (Форматный символ)
    'Cs': Other, Surrogate (Замещающий символ)
    'Co': Other, Private Use (Символ для частного использования)
    'Cn': Other, Not Assigned (Не назначен)'''
def text_normalize(text):
    text = ''.join(char for char in unicodedata.normalize('NFD', text)
                   if unicodedata.category(char) != 'Mn')  # Strip accents

    text = text.lower()
    text = re.sub("[^{}]".format(vocab), " ", text)
    text = re.sub("[ ]+", " ", text)
    return text


def read_metadata(metadata_file):
    fnames, text_lengths, texts = [], [], []
    transcript = os.path.join(metadata_file)
    lines = codecs.open(transcript, 'r', 'utf-8').readlines()
    for line in lines:
        fname, _, text = line.strip().split("|")

        fnames.append(fname)

        text = text_normalize(text) + "E"  # E: EOS
        text = [char2idx[char] for char in text]
        text_lengths.append(len(text))
        texts.append(np.array(text, np.longlong))

    return fnames, text_lengths, texts


def get_test_data(sentences, max_n):
    normalized_sentences = [text_normalize(line).strip() + "E" for line in sentences]  # text normalization, E: EOS
    texts = np.zeros((len(normalized_sentences), max_n + 1), np.longlong)
    for i, sent in enumerate(normalized_sentences):
        texts[i, :len(sent)] = [char2idx[char] for char in sent]
    return texts


class LJSpeech(Dataset):
    def __init__(self, keys, dir_name='LJSpeech-1.1'):
        self.keys = keys
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)), dir_name)
        self.fnames, self.text_lengths, self.texts = read_metadata(os.path.join(self.path, 'metadata.csv'))

    def slice(self, start, end):
        self.fnames = self.fnames[start:end]
        self.text_lengths = self.text_lengths[start:end]
        self.texts = self.texts[start:end]

    def __len__(self):
        return len(self.fnames)

    def __getitem__(self, index):
        data = {}
        if 'texts' in self.keys:
            data['texts'] = self.texts[index]
        if 'mels' in self.keys:
            # (39, 80)
            data['mels'] = np.load(os.path.join(self.path, 'mels', "%s.npy" % self.fnames[index]))
        if 'mags' in self.keys:
            # (39, 80)
            data['mags'] = np.load(os.path.join(self.path, 'mags', "%s.npy" % self.fnames[index]))
        if 'mel_gates' in self.keys:
            data['mel_gates'] = np.ones(data['mels'].shape[0], dtype=np.int32)  # TODO: because pre processing!
        if 'mag_gates' in self.keys:
            data['mag_gates'] = np.ones(data['mags'].shape[0], dtype=np.int32)  # TODO: because pre processing!
        return data