import secrets
import string


def cut_sentence(sentence, target_word):
    words = sentence.split()
    index_of_target = words.index(target_word)
    truncated_sentence = " ".join(words[: index_of_target + 1])
    return truncated_sentence


def generate_random_alphanumeric_string(length=6):
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(length))
    return random_string