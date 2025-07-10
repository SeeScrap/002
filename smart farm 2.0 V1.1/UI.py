import time
import os
from colorama import Fore, Style, init

def UI():
    init(autoreset=True)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(Fore.GREEN + "            Smart Farm 2.0 System V1.0" + Style.RESET_ALL)
    ##print(Fore.YELLOW + "            Developed by: Your Name " + Style.RESET_ALL)