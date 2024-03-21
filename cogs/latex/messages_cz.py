from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    latex_help = f"Příklad:\n`{GlobalMessages.prefix}latex [?fg=blue] x^n + y^n = z^n`"
    latex_desc = "Vykreslí LaTeX výraz"
    latex_colors = """**Možné barvy textu:**
    Transparent White Black Blue Cyan Green Magenta Red Yellow Orange Maroon NavyBlue RoyalBlue
    ProcessBlue SkyBlue Turquoise TealBlue Aquamarine BlueGreen Sepia Brown Tan Gray Fuchsia
    Lavender Purple Plum Violet GreenYellow Goldenrod Dandelion Apricot Peach Melon YellowOrange
    BurntOrange Bittersweet RedOrange Mahogany BrickRed OrangeRed RubineRed WildStrawberry Salmon
    CarnationPink VioletRed Rhodamine Mulberry RedViolet Thistle Orchid DarkOrchid RoyalPurple BlueViolet
    Periwinkle CadetBlue CornflowerBlue MidnightBlue Cerulean Emerald JungleGreen SeaGreen ForestGreen
    PineGreen LimeGreen YellowGreen SpringGreen OliveGreen RawSienna"""
