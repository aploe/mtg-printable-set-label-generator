import argparse
import base64
import logging
import os
from datetime import datetime
from pathlib import Path

import jinja2
import requests


log = logging.getLogger(__name__)

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
CAIRO_DLL_DIR = r'C:\Program Files\GTK3-Runtime Win64\bin'

ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(BASE_DIR / "templates"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)

# Windows-specific: Before importing cairosvg, need to add cairo dlls, otherwise importing fails
# https://github.com/Kozea/CairoSVG/issues/392#issuecomment-1631288142
getattr(os, 'add_dll_directory', lambda _: None)(CAIRO_DLL_DIR)
import cairosvg

# Set types we are interested in
SET_TYPES = (
    "core",             # https://scryfall.com/sets?type=core
    "expansion",        # https://scryfall.com/sets?type=expansion
    "starter",          # Portal, P3k, welcome decks // https://scryfall.com/sets?type=starter
    "masters",          # https://scryfall.com/sets?type=masters
    "commander",        # https://scryfall.com/sets?type=commander
    "planechase",       # https://scryfall.com/sets?type=planechase
    "draft_innovation", # Battlebond, Conspiracy // https://scryfall.com/sets?type=draft_innovation
    "duel_deck",        # Duel Deck Elves // https://scryfall.com/sets?type=duel_deck
    # "premium_deck",     # Premium Deck Series: Slivers, Premium Deck Series: Graveborn // https://scryfall.com/sets?type=premium_deck
    "from_the_vault",   # Make sure to adjust the MINIMUM_SET_SIZE if you want these // https://scryfall.com/sets?type=from_the_vault
    "archenemy",        # https://scryfall.com/sets?type=archenemy
    # "box",              # https://scryfall.com/sets?type=box
    "funny",            # Unglued, Unhinged, Ponies: TG, etc. // https://scryfall.com/sets?type=funny
    # "minigame",      # https://scryfall.com/sets?type=minigame
    # "memorabilia",      # Commander's Arsenal, Celebration Cards, World Champ Decks // https://scryfall.com/sets?type=memorabilia
    # "spellbook",        # https://scryfall.com/sets?type=spellbook
    # These are relatively large groups of sets
    # You almost certainly don't want these
    # "token",            # https://scryfall.com/sets?type=token
    # "promo",            # https://scryfall.com/sets?type=promo
)

# Only include sets at least this size
# For reference, the smallest proper expansion is Arabian Nights with 78 cards
MINIMUM_SET_SIZE = 10

# Set codes you might want to ignore
IGNORED_SETS = (
    "DA1",  # Mystery Booster Playtest Cards
    # "cmb1",  # Mystery Booster Playtest Cards
    # "amh1",  # Modern Horizon Art Series
    # "cmb2",  # Mystery Booster Playtest Cards Part Deux
)

# Used to rename very long set names
RENAME_SETS = {
    # "Bloomburrow Commander": "Bloomburrow [C]",
    # "Modern Horizons 3 Commander": "Modern Horizons 3 [C]",
    # "Brothers' War Commander": "Brothers' War [C]",
    # "New Capenna Commander": "New Capenna [C]",
    # "Forgotten Realms Commander": "Forgotten Realms [C]",

    "Adventures in the Forgotten Realms": "Forgotten Realms",
    "Adventures in the Forgotten Realms Minigames": "Forgotten Realms Minigames",
    "Angels: They're Just Like Us but Cooler and with Wings": "Angels: Just Like Us",
    "Archenemy: Nicol Bolas Schemes": "Archenemy: Bolas Schemes",
    "Chronicles Foreign Black Border": "Chronicles FBB",
    # "Commander Anthology Volume II": "Commander Anthology II",
    "Commander Legends: Battle for Baldur's Gate": "Commander Legends: Baldur's Gate",
    "Commander Legends: Battle for Baldur's Gate Minigames": "Commander Legends: Baldur's Gate Minigames",
    # "Dominaria United Commander": "Dominaria United [C]",
    # "Duel Decks: Elves vs. Goblins": "DD: Elves vs. Goblins",
    # "Duel Decks: Jace vs. Chandra": "DD: Jace vs. Chandra",
    # "Duel Decks: Divine vs. Demonic": "DD: Divine vs. Demonic",
    # "Duel Decks: Garruk vs. Liliana": "DD: Garruk vs. Liliana",
    "Duel Decks: Phyrexia vs. the Coalition": "Duel Decks: Phyrexia v Coalition",
    # "Duel Decks: Elspeth vs. Tezzeret": "DD: Elspeth vs. Tezzeret",
    # "Duel Decks: Knights vs. Dragons": "DD: Knights vs. Dragons",
    # "Duel Decks: Ajani vs. Nicol Bolas": "DD: Ajani vs. Nicol Bolas",
    # "Duel Decks: Heroes vs. Monsters": "DD: Heroes vs. Monsters",
    # "Duel Decks: Speed vs. Cunning": "DD: Speed vs. Cunning",
    "Duel Decks Anthology: Elves vs. Goblins": "Duel Decks A.: Elves vs. Goblins",
    "Duel Decks Anthology: Jace vs. Chandra": "Duel Decks A.: Jace vs. Chandra",
    "Duel Decks Anthology: Divine vs. Demonic": "Duel Decks A.: Divine vs. Demonic",
    "Duel Decks Anthology: Garruk vs. Liliana": "Duel Decks A.: Garruk vs. Liliana",
    # "Duel Decks: Elspeth vs. Kiora": "DD: Elspeth vs. Kiora",
    # "Duel Decks: Zendikar vs. Eldrazi": "DD: Zendikar vs. Eldrazi",
    # "Duel Decks: Blessed vs. Cursed": "DD: Blessed vs. Cursed",
    # "Duel Decks: Nissa vs. Ob Nixilis": "DD: Nissa vs. Ob Nixilis",
    # "Duel Decks: Merfolk vs. Goblins": "DD: Merfolk vs. Goblins",
    # "Duel Decks: Elves vs. Inventors": "DD: Elves vs. Inventors",
    "Duel Decks: Mirrodin Pure vs. New Phyrexia": "DD: Mirrodin vs. New Phyrexia",
    # "Duel Decks: Izzet vs. Golgari": "DD: Izzet vs. Golgari",
    "Duskmourn: House of Horror Commander": "Duskmourn: House of Horror [C]",
    "Fourth Edition Foreign Black Border": "Fourth Edition FBB",
    "Global Series Jiang Yanggu & Mu Yanling": "Jiang Yanggu & Mu Yanling",
    "Innistrad: Crimson Vow Minigames": "Crimson Vow Minigames",
    # "Introductory Two-Player Set": "Intro Two-Player Set",
    "March of the Machine: The Aftermath": "MotM: The Aftermath",
    # "March of the Machine Commander": "March of the Machine [C]",
    "Murders at Karlov Manor Commander": "Murders at Karlov Manor [C]",
    "Mystery Booster Playtest Cards": "Mystery Booster Playtest",
    "Mystery Booster Playtest Cards 2019": "MB Playtest Cards 2019",
    "Mystery Booster Playtest Cards 2021": "MB Playtest Cards 2021",
    "Mystery Booster Retail Edition Foils": "Mystery Booster Retail Foils",
    "Outlaws of Thunder Junction Commander": "Outlaws of Thunder Junction [C]",
    "Phyrexia: All Will Be One Commander": "Phyrexia: All Will Be One [C]",
    # "Planechase Anthology Planes": "Planechase Anth. Planes",
    "Premium Deck Series: Slivers": "Premium Deck: Slivers",
    "Premium Deck Series: Graveborn": "Premium Deck: Graveborn",
    "Premium Deck Series: Fire and Lightning": "Premium Deck: Fire & Lightning",
    "Shadows over Innistrad Remastered": "Shadows o Innistrad Remastered",
    "Strixhaven: School of Mages Minigames": "Strixhaven Minigames",
    # "Tales of Middle-earth Commander": "Tales of Middle-earth [C]",
    "The Brothers' War Retro Artifacts": "Brothers' War Retro Artifacts",
    "The Brothers' War Commander": "Brothers' War Commander",
    "The Lord of the Rings: Tales of Middle-earth": "LOTR: Tales of Middle-earth",
    "The Lost Caverns of Ixalan Commander": "The Lost Caverns of Ixalan [C]",
    # "Warhammer 40,000 Commander": "Warhammer 40K [C]",
    # "Wilds of Eldraine Commander": "Wilds of Eldraine [C]",
    "World Championship Decks 1997": "World Championship 1997",
    "World Championship Decks 1998": "World Championship 1998",
    "World Championship Decks 1999": "World Championship 1999",
    "World Championship Decks 2000": "World Championship 2000",
    "World Championship Decks 2001": "World Championship 2001",
    "World Championship Decks 2002": "World Championship 2002",
    "World Championship Decks 2003": "World Championship 2003",
    "World Championship Decks 2004": "World Championship 2004",
}


class LabelGenerator:

    DEFAULT_OUTPUT_DIR = Path(os.getcwd()) / "output"
    DEFAULT_MARGIN = 200
    DEFAULT_MARGIN_INNER = 30

    PAPER_SIZES = {
        "letter": {
            "width": 2790,
            "height": 2160,
            "cols": 4,
            "rows": 15,
        },
        "a4": {
            "width": 2970,
            "height": 2100,
            "cols": 4,
            "rows": 15,
        },
        "a4-vertical": {
            "width": 2100,
            "height": 2970,
            "cols": 3,
            "rows": 15,
        },
        "avery-60x25-R": {
            "width": 2100,
            "height": 2970,
            "cols": 3,
            "rows": 9,
            # Page margins
            "page-margin-width": 90,
            "page-margin-height": 120,
            # Margin of the print labels
            "margin": 60,
            # Inner margin of each label
            "margin-inner-width": 50,
            "margin-inner-height": 40,
        },
    }
    DEFAULT_PAPER_SIZE = "a4"


    def __init__(self, paper_size=DEFAULT_PAPER_SIZE, output_dir=DEFAULT_OUTPUT_DIR):
        self.paper_size = paper_size
        paper = self.PAPER_SIZES[paper_size]

        self.set_codes = []
        self.ignored_sets = IGNORED_SETS
        self.set_types = SET_TYPES
        self.minimum_set_size = MINIMUM_SET_SIZE

        self.width = paper["width"]
        self.height = paper["height"]
        self.COLS = paper["cols"]
        self.ROWS = paper["rows"]
        self.MARGIN = paper.get("margin", self.DEFAULT_MARGIN)
        self.MARGIN_X = paper.get("margin-x", self.MARGIN)
        self.MARGIN_Y = paper.get("margin-y", self.MARGIN)
        self.START_X = paper.get("page-margin-width", self.MARGIN_X)
        self.START_Y = paper.get("page-margin-height", self.MARGIN_Y)
        self.MARGIN_INNER = paper.get("margin-inner", self.DEFAULT_MARGIN)
        self.MARGIN_INNER_X = paper.get("margin-inner-width", self.MARGIN_INNER)
        self.MARGIN_INNER_Y = paper.get("margin-inner-height", self.MARGIN_INNER)

        # Calc new start coords by accounting for page margins
        self.START_X = self.START_X - ( self.MARGIN_X / 2 )
        self.START_Y = self.START_Y - ( self.MARGIN_Y / 2 )

        # These are the deltas between rows and columns
        self.delta_x = (self.width - (2 * self.START_X)) / self.COLS
        self.delta_y = (self.height - (2 * self.START_Y)) / self.ROWS

        self.output_dir = Path(output_dir)

    def generate_labels(self, sets=None):
        if sets:
            self.ignored_sets = ()
            self.minimum_set_size = 0
            self.set_types = ()
            self.set_codes = [exp.lower() for exp in sets]

        page = 1
        labels = self.create_set_label_data()
        while labels:
            exps = []
            while labels and len(exps) < (self.ROWS * self.COLS):
                exps.append(labels.pop(0))

            # Render the label template
            template = ENV.get_template("labels.svg")
            output = template.render(
                labels=exps,
                horizontal_guides=self.create_horizontal_cutting_guides(),
                vertical_guides=self.create_vertical_cutting_guides(),
                WIDTH=self.width,
                HEIGHT=self.height,
                LABEL_WIDTH=self.delta_x,
                LABEL_HEIGHT=self.delta_y,
                MARGIN_INNER_X=self.MARGIN_INNER_X,
                MARGIN_INNER_Y=self.MARGIN_INNER_Y
            )
            outfile_svg = self.output_dir / f"labels-{self.paper_size}-{page:02}.svg"
            outfile_pdf = str(
                self.output_dir / f"labels-{self.paper_size}-{page:02}.pdf"
            )

            log.info(f"Writing {outfile_svg}...")
            with open(outfile_svg, "w") as fd:
                fd.write(output)

            log.info(f"Writing {outfile_pdf}...")
            with open(outfile_svg, "rb") as fd:
                cairosvg.svg2pdf(
                    file_obj=fd, write_to=outfile_pdf,
                )

            page += 1

    def get_set_data(self):
        log.info("Getting set data and icons from Scryfall")

        # https://scryfall.com/docs/api/sets
        # https://scryfall.com/docs/api/sets/all
        resp = requests.get("https://api.scryfall.com/sets")
        resp.raise_for_status()

        data = resp.json()["data"]
        set_data = []
        for exp in data:
            if exp["code"] in self.ignored_sets:
                continue
            elif exp["card_count"] < self.minimum_set_size:
                continue
            elif self.set_types and exp["set_type"] not in self.set_types:
                continue
            elif self.set_codes and exp["code"].lower() not in self.set_codes:
                # Scryfall set codes are always lowercase
                continue
            else:
                set_data.append(exp)

        # Warn on any unknown set codes
        if self.set_codes:
            known_sets = set([exp["code"] for exp in data])
            specified_sets = set([code.lower() for code in self.set_codes])
            unknown_sets = specified_sets.difference(known_sets)
            for set_code in unknown_sets:
                log.warning("Unknown set '%s'", set_code)

        set_data.reverse()
        return set_data

    def create_set_label_data(self):
        """
        Create the label data for the sets

        This handles positioning of the label's (x, y) coords
        """
        labels = []
        x = self.START_X
        y = self.START_Y

        # Get set data from scryfall
        set_data = self.get_set_data()

        for exp in set_data:
            name = RENAME_SETS.get(exp["name"], exp["name"])
            icon_resp = requests.get(exp["icon_svg_uri"])
            icon_b64 = None
            if icon_resp.ok:
                icon_b64 = base64.b64encode(icon_resp.content).decode('utf-8')

            labels.append(
                {
                    "name": name,
                    "code": exp["code"],
                    "date": datetime.strptime(exp["released_at"], "%Y-%m-%d").date(),
                    "icon_url": exp["icon_svg_uri"],
                    "icon_b64": icon_b64,
                    "x": x,
                    "y": y,
                }
            )

            y += self.delta_y

            # Start a new column if needed
            if len(labels) % self.ROWS == 0:
                x += self.delta_x
                y = self.START_Y

            # Start a new page if needed
            if len(labels) % (self.ROWS * self.COLS) == 0:
                x = self.START_X
                y = self.START_Y

        return labels

    def create_horizontal_cutting_guides(self):
        """Create horizontal cutting guides to help cut the labels out straight"""
        horizontal_guides = []
        for i in range(self.ROWS + 1):
            horizontal_guides.append(
                {
                    "x1": self.START_X / 2,
                    "x2": self.START_X * 0.8,
                    "y1": self.START_Y + i * self.delta_y,
                    "y2": self.START_Y + i * self.delta_y,
                }
            )
            horizontal_guides.append(
                {
                    "x1": self.width - self.START_X / 2,
                    "x2": self.width - self.START_X * 0.8,
                    "y1": self.START_Y + i * self.delta_y,
                    "y2": self.START_Y + i * self.delta_y,
                }
            )

        return horizontal_guides

    def create_vertical_cutting_guides(self):
        """Create horizontal cutting guides to help cut the labels out straight"""
        vertical_guides = []
        for i in range(self.COLS + 1):
            vertical_guides.append(
                {
                    "x1": self.START_X + i * self.delta_x,
                    "x2": self.START_X + i * self.delta_x,
                    "y1": self.START_Y / 2,
                    "y2": self.START_Y * 0.8,
                }
            )
            vertical_guides.append(
                {
                    "x1": self.START_X + i * self.delta_x,
                    "x2": self.START_X + i * self.delta_x,
                    "y1": self.height - self.START_Y / 2,
                    "y2": self.height - self.START_Y * 0.8,
                }
            )

        return vertical_guides


def main():
    log_format = '[%(levelname)s] %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)

    parser = argparse.ArgumentParser(description="Generate MTG labels")

    parser.add_argument(
        "--output-dir",
        default=LabelGenerator.DEFAULT_OUTPUT_DIR,
        help="Output labels to this directory",
    )
    parser.add_argument(
        "--paper-size",
        default=LabelGenerator.DEFAULT_PAPER_SIZE,
        choices=LabelGenerator.PAPER_SIZES.keys(),
        help='Use this paper size (default: "letter")',
    )
    parser.add_argument(
        "sets",
        nargs="*",
        help=(
            "Only output sets with the specified set code (eg. MH1, NEO). "
            "This can be used multiple times."
        ),
        metavar="SET",
    )

    args = parser.parse_args()

    generator = LabelGenerator(args.paper_size, args.output_dir)
    generator.generate_labels(args.sets)


if __name__ == "__main__":
    main()
