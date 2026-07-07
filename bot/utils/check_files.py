import os

def check_files():
    """
    checks if required files exist
    """
    slur_path = os.path.join('bot', 'helpers', 'slurs.txt')

    if not os.path.exists(slur_path):
        open(slur_path, 'w')
