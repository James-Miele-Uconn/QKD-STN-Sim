import os

# Javascript needed for changing theme mode
def theme_mode_js():
    return """
    () => {
        document.body.classList.toggle('dark');
    }
    """


# Update theme color
def update_theme_color(cur_color):
    if not os.path.exists("./customization"):
        try:
            os.mkdir("./customization")
        except:
            pass

    with open("./customization/theme_color.txt", "w", encoding="utf-8") as outf:
        outf.write(cur_color)