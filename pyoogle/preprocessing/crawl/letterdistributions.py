
import numpy as np
from numpy.linalg import norm

# Distributions of letters A-Z,ß,Ä,Ö,Ü in some languages according to wikipedia
_LETTER_DISTRIBUTION_LENGTH = 30  # letter distributions must have this length


def _letter_index(letter):
    index = ord(letter) - ord('A')
    if 0 <= index < 26:
        return index
    if letter == "ß":
        return 26
    if letter == "Ä":
        return 27
    if letter == "Ö":
        return 28
    if letter == "Ü":
        return 29
    return -1


_LETTER_DISTRIBUTIONS = {'de': np.array((6.51, 1.89, 3.06, 5.08, 17.4, 1.66, 3.01, 4.76, 7.55, 0.27, 1.21, 3.44, 2.53,
                                        9.78, 2.51, 0.79, 0.02, 7.00, 7.27, 6.15, 4.35, 0.67, 1.89, 0.03, 0.04, 1.13,
                                        0.31, 0.54, 0.3, 0.65)) / 100,
                         'en': np.array((8.167, 1.492, 2.782, 4.253, 12.702, 2.228, 2.015, 6.094, 6.966, 0.153, 0.772,
                                        4.025, 2.406, 6.749, 7.507, 1.929, 0.095, 5.987, 6.327, 9.056, 2.758, 0.978,
                                        2.361, 0.150, 1.974, 0.074, 0, 0, 0, 0)) / 100}


def _add_letter(distribution, letter):
    letter_index = _letter_index(letter)
    if 0 <= letter_index < _LETTER_DISTRIBUTION_LENGTH:
        distribution[letter_index] += 1


def _guess_language(text):
    distribution = np.zeros(_LETTER_DISTRIBUTION_LENGTH)
    content = "".join(text).upper()
    for letter in content:
        _add_letter(distribution, letter)
    distribution /= len(content)

    languages = list(_LETTER_DISTRIBUTIONS)
    differences = [norm(distribution - _LETTER_DISTRIBUTIONS[language]) for language in languages]
    return languages[differences.index(min(differences))]

if __name__ == "__main__":
    # de
    print(_guess_language("Hallo ehrlich esel eigentlich. Wie geht es dir das ist eine Testnachricht. "
                          "Du bist immer dann am besten, jedes Mal. Dein Spiegelbild ist anderen egal"))
    # en
    print(_guess_language("Hello whats up, this is my test message, I'm Daniel"))
