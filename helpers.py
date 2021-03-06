import eventlet
import random
from classes.player import Player
eventlet.monkey_patch()
color_dict = {"black": [0, 0, 0], "dimgray": [105, 105, 105], "purple": [128, 0, 128], "red": [255, 0, 0],
              "blue": [0, 0, 255], "green": [0, 128, 0], "orange": [255, 165, 0], "white": [255, 255, 255],
              "darkgray": [169, 169, 169], "pink": [255, 192, 203], "salmon": [250, 128, 114], "cyan": [0, 255, 255],
              "palegreen": [152, 251, 152], "yellow": [255, 255, 0]}


def validate_color(color_name):
    """ ensures the color_name exists in the color dict """
    return color_name in list(color_dict.keys())


def validate_width(width):
    """ Validates the the width is an int within 1 and 10 """
    try:
        w = int(width)
        return 1 <= w <= 10
    except ValueError:
        return False


def get_prohibited_words():
    """ Returns all words that are prohibited """
    lst = []
    with open('static/words/prohibited.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            lst.append(line.rstrip())
    with open('static/words/language_filter.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            lst.append(line.rstrip())
    return lst


def get_prohibited_chars():
    """ Returns all chars that are prohibited """
    return ["<", ">", ":", "\"", "{", "}"]


def get_color_by_name(color_name):
    """ Returns the rgb value of the color """
    c = color_dict.get(color_name, [0, 0, 0])
    cJson = {'r': c[0], 'g': c[1], 'b': c[2]}
    return cJson


def getRandomNumbers(cap, amount):
    """ Returns a list with 'amount' random different numbers between 0 and cap (including)"""
    available = list(range(cap + 1))  # from 0 to cap
    # print(available)
    my_nums = []
    for j in range(amount):
        if j > cap:
            return my_nums
        val = available.pop(random.randint(0, len(available) - 1))
        my_nums.append(val)
    return my_nums


def get_full_image_path(user):
    """ Returns the path of an image. Note: all images are saved via png """
    if user:
        return "/static/Images/" + user.image + ".png"
    return "/static/Images/anonymous.png"


def player_list_to_dict(player_list, with_scores, with_image=True):
    """ returns a dict of players according to the given parameters """
    my_dict = dict()
    for player in player_list:
        if with_scores and with_image:
            my_dict[player.username] = (player.score, get_full_image_path(player.user))
        elif with_scores:
            my_dict[player.username] = player.score
        elif with_image:
            my_dict[player.username] = get_full_image_path(player.user)
    return my_dict


def sort_player_dict(dicti):
    """ sorts the dict based on points """
    sort_lst = sorted(dicti.items(), key=lambda x: x[1][0], reverse=True)
    sorted_dict = dict()
    for key,value in sort_lst:
        sorted_dict[key] = value
    return sorted_dict


def sort_player_dict_without_images(dicti):
    """ sorts the dict based on points """
    sort_lst = sorted(dicti.items(), key=lambda x: x[1], reverse=True)
    sorted_dict = dict()
    for key,value in sort_lst:
        sorted_dict[key] = value
    return sorted_dict


def is_valid_text(my_string):
    """ Returns True if the given string does not contain any prohibited chars or words, else False """
    proh_chars = get_prohibited_chars()
    for c in proh_chars:
        if c in my_string:
            return False
    proh_words = get_prohibited_words()
    for word in proh_words:
        if word in my_string:
            return False
    return True
