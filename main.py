#!/usr/bin/env python3
import os
import time
import pyfiglet

# Colors
Wh = '\033[1;37m'
Gr = '\033[1;32m'
Cy = '\033[1;36m'
Re = '\033[1;31m'
reset = '\033[0m'

BANNER_ART  = R"""
 $$$$$$\                             $$$$$$$$\ $$\            $$\     
$$  __$$\                            \__$$  __|$$ |           $$ |    
$$ /  \__| $$$$$$\  $$\   $$\ $$$$$$$\  $$ |   $$ | $$$$$$\ $$$$$$\   
$$ |$$$$\  \____$$\ $$ |  $$ |$$  __$$\ $$ |   $$ |$$  __$$\\_$$  _|  
$$ |\_$$ | $$$$$$$ |$$ |  $$ |$$ |  $$ |$$ |   $$ |$$$$$$$$ | $$ |    
$$ |  $$ |$$  __$$ |$$ |  $$ |$$ |  $$ |$$ |   $$ |$$   ____| $$ |$$\ 
\$$$$$$  |\$$$$$$$ |\$$$$$$  |$$ |  $$ |$$ |   $$ |\$$$$$$$\  \$$$$  |
 \______/  \_______| \______/ \__|  \__|\__|   \__| \_______|  \____/ 
                                                                      
                                                                      
                                                                      
"""


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    print(f"{Cy}{BANNER_ART}{reset}")
    print(f"{Wh}--------------------------------------------")
    print(f"{Gr} A python testing tool for session managment and web application security testing")
    print(f"{Wh}--------------------------------------------{reset}")


def option_text(options):
    text = ""
    for opt in options:
        text += f"{Wh}[ {opt['num']} ] {Gr}{opt['text']}\n"
    return text


def is_in_options(options, num):
    return any(opt['num'] == num for opt in options)


def call_option(options, num):
    if not is_in_options(options, num):
        raise ValueError("Option not found")
    for opt in options:
        if opt['num'] == num:
            opt['func']()
            return


def execute_option(options, num):
    try:
        call_option(options, num)
        input(f"\n{Wh}[ {Gr}+ {Wh}] {Gr}Press enter to continue{reset}")
    except ValueError as e:
        print(f"{Re}{e}{reset}")
        time.sleep(1.5)
    except KeyboardInterrupt:
        print(f"\n{Wh}[ {Re}! {Wh}] {Re}Exit{reset}")
        time.sleep(1)
        raise SystemExit


def show_menu(options):
    clear()
    show_banner()
    print(f"\n{option_text(options)}")


def run_menu(options):
    while True:
        show_menu(options)
        try:
            choice = int(input(f"{Wh}\n [ + ] {Gr}Select option: {Wh}"))
        except ValueError:
            print(f"\n{Wh}[ {Re}! {Wh}] {Re}Please enter a number{reset}")
            time.sleep(1.5)
            continue
        execute_option(options, choice)


# ---- define your own options here ----
def example_action():
    print(f"\n{Gr}Ran example action.{reset}")


options = [
    {'num': 1, 'text': 'Example action', 'func': example_action},
    {'num': 0, 'text': 'Exit', 'func': lambda: (_ for _ in ()).throw(SystemExit)},
]


if __name__ == '__main__':
    try:
        run_menu(options)
    except (KeyboardInterrupt, SystemExit):
        print(f"\n{Wh}[ {Re}! {Wh}] {Re}Exit{reset}")
        time.sleep(1)                   
                                                                      